# ============================================================
# EXECUTOR - ORQUESTRADOR CENTRAL DO SISTEMA
# ============================================================
# Responsável por:
# - Coordenar o fluxo completo do sistema
# - Integrar coleta de dados, scoring e execução
# - Registrar decisões no banco
# ============================================================

import time
from typing import Dict

from app.core.logger import logger
from app.core.config import EXECUTION_CONFIG

from app.infrastructure.market_data.coleta_dados import pegar_dados_reais
from app.infrastructure.market_data.tratamento_dados import processar_dados

from app.domain.scoring import calcular_score_completo, gerar_decisao

from app.execution.broker_simulado import executar_ordem, calcular_patrimonio

from app.database.connection import execute_query


# ============================================================
# MAPEAMENTO DE ATIVOS
# ============================================================

def obter_ativo_id(ticker: str) -> int:

    query = "SELECT id FROM ativos WHERE ticker = %s"

    result = execute_query(query, (ticker,), fetch=True)

    if result:
        return result[0][0]

    insert = "INSERT INTO ativos (ticker) VALUES (%s) RETURNING id"

    result = execute_query(insert, (ticker,), fetch=True)

    return result[0][0]


# ============================================================
# PROCESSAR UM ATIVO
# ============================================================

def processar_ativo(row: Dict):

    try:

        ticker = row["ativo"]

        preco = row["preco"]

        ativo_id = obter_ativo_id(ticker)

        # ====================================================
        # SCORING
        # ====================================================

        score_data = calcular_score_completo(row)

        score_total = score_data["score_total"]

        decisao = gerar_decisao(score_total)

        # ====================================================
        # REGISTRAR SCORE
        # ====================================================

        execute_query("""
            INSERT INTO scores (
                ativo_id,
                score_total,
                score_fundamentos,
                score_momento,
                score_risco,
                score_liquidez,
                decisao
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
        # EXECUÇÃO
        # ====================================================

        if decisao == "COMPRA":

            executar_ordem(
                ativo_id=ativo_id,
                tipo="COMPRA",
                preco=preco,
                quantidade=EXECUTION_CONFIG.quantidade_padrao,
                score=score_total
            )

        elif decisao == "VENDA":

            executar_ordem(
                ativo_id=ativo_id,
                tipo="VENDA",
                preco=preco,
                quantidade=EXECUTION_CONFIG.quantidade_padrao,
                score=score_total
            )

        logger.info(
            f"[EXECUTOR] {ticker} | Score {score_total:.2f} | {decisao}"
        )

    except Exception as e:

        logger.error(
            f"[EXECUTOR] Erro no ativo {row.get('ativo')}: {e}"
        )


# ============================================================
# EXECUÇÃO COMPLETA
# ============================================================

def executar_ciclo():

    logger.info("========================================")
    logger.info("[EXECUTOR] Iniciando ciclo")
    logger.info("========================================")

    try:

        # ====================================================
        # COLETA DE DADOS
        # ====================================================

        df = pegar_dados_reais()

        if df.empty:

            logger.warning(
                "[EXECUTOR] Nenhum dado coletado"
            )

            return

        # ====================================================
        # TRATAMENTO
        # ====================================================

        df = processar_dados(df)

        # ====================================================
        # EXECUÇÃO
        # ====================================================

        for _, row in df.iterrows():

            processar_ativo(row)

        # ====================================================
        # ATUALIZAR PATRIMÔNIO
        # ====================================================

        precos = {
            row["ativo"]: row["preco"]
            for _, row in df.iterrows()
        }

        patrimonio = calcular_patrimonio(precos)

        logger.info(
            f"[EXECUTOR] Patrimônio atualizado: {patrimonio:.2f}"
        )

    except Exception as e:

        logger.error(
            f"[EXECUTOR] Erro geral no ciclo: {e}"
        )


# ============================================================
# LOOP CONTÍNUO
# ============================================================

def executar_loop():

    intervalo = EXECUTION_CONFIG.intervalo_segundos

    logger.info(
        f"[EXECUTOR] Loop iniciado | Intervalo={intervalo}s"
    )

    while True:

        try:

            executar_ciclo()

        except Exception as e:

            logger.error(
                f"[EXECUTOR] Falha no loop: {e}"
            )

        time.sleep(intervalo)