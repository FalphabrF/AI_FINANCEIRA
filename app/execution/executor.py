# ============================================================

# EXECUTOR - ORQUESTRADOR CENTRAL DO SISTEMA

# ============================================================

# Responsável por:

# - Coordenar todo o fluxo do sistema

# - Executar pipeline completo de decisão

# - Integrar todos os módulos

#

# PIPELINE:

# 1. Coleta de dados

# 2. Tratamento de dados

# 3. Geração de score

# 4. Decisão

# 5. Execução via broker

# 6. Registro no banco

#

# DIFERENCIAL:

# - Sistema totalmente automatizado

# - Controle de falhas

# - Logs completos

# ============================================================

import time
from typing import Dict

from core.logger import logger
from core.config import EXECUTION_CONFIG

from data.coleta_dados import pegar_dados_reais
from data.tratamento_dados import processar_dados

from models.scoring import calcular_score_completo, gerar_decisao

from execution.broker_simulado import executar_ordem, calcular_patrimonio
from core.connection import execute_query

# ============================================================

# MAPEAMENTO DE ATIVOS

# ============================================================

def obter_ativo_id(ticker: str) -> int:
    """
    Busca ID do ativo no banco.
    """

    query = "SELECT id FROM ativos WHERE ticker = %s"
    result = execute_query(query, (ticker,), fetch=True)

    if result:
        return result[0][0]

    # Criar ativo se não existir
    insert = "INSERT INTO ativos (ticker) VALUES (%s) RETURNING id"
    result = execute_query(insert, (ticker,), fetch=True)

    return result[0][0]

# ============================================================

# PROCESSAR UM ATIVO

# ============================================================

def processar_ativo(row: Dict):
    """
    Executa pipeline completo para um ativo.
    """

    try:
        ticker = row["ativo"]
        ativo_id = obter_ativo_id(ticker)

        # ====================================================
        # SCORING
        # ====================================================
        score_data = calcular_score_completo(row)

        score_total = score_data["score_total"]
        decisao = gerar_decisao(score_total)

        # Registrar score
        execute_query("""
            INSERT INTO scores (
                ativo_id, score_total, score_fundamentos,
                score_momento, score_risco, score_liquidez, decisao
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (
            ativo_id,
            score_total,
            score_data["fundamentos"],
            score_data["momento"],
            score_data["risco"],
            score_data["liquidez"],
            decisao
        ))

        # ====================================================
        # DECISÃO
        # ====================================================
        if decisao == "COMPRA":

            executar_ordem(
                ativo_id=ativo_id,
                tipo="COMPRA",
                preco=row["preco"],
                quantidade=EXECUTION_CONFIG.quantidade_padrao,
                score=score_total
            )

        elif decisao == "VENDA":

            executar_ordem(
                ativo_id=ativo_id,
                tipo="VENDA",
                preco=row["preco"],
                quantidade=EXECUTION_CONFIG.quantidade_padrao,
                score=score_total
            )

        logger.info(f"[EXECUTOR] {ticker} | Score {score_total:.2f} | {decisao}")

    except Exception as e:
        logger.error(f"[EXECUTOR] Erro no ativo {row.get('ativo')}: {e}")

# ============================================================

# EXECUÇÃO COMPLETA

# ============================================================

def executar_ciclo():
    """
    Executa um ciclo completo do sistema.
    """

    logger.info("========================================")
    logger.info("[EXECUTOR] Iniciando ciclo")
    logger.info("========================================")

    try:
        # ====================================================
        # 1. COLETA
        # ====================================================
        df = pegar_dados_reais()

        if df.empty:
            logger.warning("[EXECUTOR] Nenhum dado coletado")
            return

        # ====================================================
        # 2. TRATAMENTO
        # ====================================================
        df = processar_dados(df)

        # ====================================================
        # 3. EXECUÇÃO POR ATIVO
        # ====================================================
        for _, row in df.iterrows():
            processar_ativo(row)

        # ====================================================
        # 4. ATUALIZAR PATRIMÔNIO
        # ====================================================
        precos = {row["ativo"]: row["preco"] for _, row in df.iterrows()}
        patrimonio = calcular_patrimonio(precos)

        logger.info(f"[EXECUTOR] Patrimônio atualizado: {patrimonio:.2f}")

    except Exception as e:
        logger.error(f"[EXECUTOR] Erro geral no ciclo: {e}")

# ============================================================

# LOOP CONTÍNUO

# ============================================================

def executar_loop():
    """
    Loop contínuo do sistema.
    """

    intervalo = EXECUTION_CONFIG.intervalo_segundos

    logger.info(f"[EXECUTOR] Loop iniciado | Intervalo: {intervalo}s")

    while True:
        try:
            executar_ciclo()

        except Exception as e:
            logger.error(f"[EXECUTOR] Falha no loop: {e}")

        time.sleep(intervalo)
