# ============================================================

# BROKER SIMULADO - EXECUÇÃO REALISTA DE ORDENS

# ============================================================

# Responsável por:

# - Simular execução de ordens

# - Controlar capital

# - Gerenciar posições

# - Registrar operações no banco

#

# DIFERENCIAIS:

# - Slippage (diferença de preço)

# - Taxas simuladas

# - Controle de saldo

# - Persistência completa

# ============================================================

import uuid
import random
from datetime import datetime

from core.connection import execute_query, fetch_dataframe, transacao
from core.logger import logger

# ============================================================

# CONFIGURAÇÕES DO BROKER

# ============================================================

TAXA_CORRETAGEM = 0.001  # 0.1%
SLIPPAGE_MAX = 0.002     # 0.2%

# ============================================================

# UTILIDADES

# ============================================================

def aplicar_slippage(preco: float) -> float:
    """
    Aplica variação de preço simulando mercado real.
    """
    variacao = random.uniform(-SLIPPAGE_MAX, SLIPPAGE_MAX)
    return preco * (1 + variacao)

# ============================================================

# CAPITAL

# ============================================================

def obter_capital():
    """
    Retorna estado atual do capital.
    """

    query = """
        SELECT capital_total, capital_disponivel, capital_investido
        FROM capital
        ORDER BY atualizado_em DESC
        LIMIT 1
    """

    result = execute_query(query, fetch=True)

    if not result:
        raise ValueError("Capital não inicializado")

    return result[0]

def atualizar_capital(total, disponivel, investido):
    """
    Atualiza capital no banco.
    """

    query = """
        INSERT INTO capital (capital_total, capital_disponivel, capital_investido)
        VALUES (%s, %s, %s)
    """

    execute_query(query, (total, disponivel, investido))

# ============================================================

# POSIÇÕES

# ============================================================

def obter_posicao(ativo_id):
    """
    Retorna posição atual de um ativo.
    """

    query = """
        SELECT quantidade, preco_medio
        FROM posicoes
        WHERE ativo_id = %s
    """

    result = execute_query(query, (ativo_id,), fetch=True)

    if result:
        return result[0]

    return (0, 0)

def atualizar_posicao(ativo_id, quantidade, preco):
    """
    Atualiza posição do ativo.
    """

    atual = obter_posicao(ativo_id)

    qtd_atual, preco_medio = atual

    nova_qtd = qtd_atual + quantidade

    if nova_qtd == 0:
        # Zerar posição
        query = "DELETE FROM posicoes WHERE ativo_id = %s"
        execute_query(query, (ativo_id,))
        return

    novo_preco_medio = (
        (qtd_atual * preco_medio + quantidade * preco) / nova_qtd
        if qtd_atual > 0 else preco
    )

    query = """
        INSERT INTO posicoes (ativo_id, quantidade, preco_medio)
        VALUES (%s, %s, %s)
        ON CONFLICT (ativo_id)
        DO UPDATE SET
            quantidade = EXCLUDED.quantidade,
            preco_medio = EXCLUDED.preco_medio,
            atualizado_em = CURRENT_TIMESTAMP
    """

    execute_query(query, (ativo_id, nova_qtd, novo_preco_medio))

# ============================================================

# EXECUÇÃO DE ORDENS

# ============================================================

def executar_ordem(ativo_id, tipo, preco, quantidade, score):
    """
    Executa ordem simulada.
    """

    preco_execucao = aplicar_slippage(preco)
    valor_total = preco_execucao * quantidade
    taxa = valor_total * TAXA_CORRETAGEM

    capital_total, capital_disp, capital_inv = obter_capital()

    ordem_id = str(uuid.uuid4())

    with transacao() as cursor:

        if tipo == "COMPRA":

            custo_total = valor_total + taxa

            if capital_disp < custo_total:
                raise ValueError("Capital insuficiente")

            capital_disp -= custo_total
            capital_inv += valor_total

            atualizar_posicao(ativo_id, quantidade, preco_execucao)

        elif tipo == "VENDA":

            qtd_atual, _ = obter_posicao(ativo_id)

            if qtd_atual < quantidade:
                raise ValueError("Quantidade insuficiente")

            receita = valor_total - taxa

            capital_disp += receita
            capital_inv -= valor_total

            atualizar_posicao(ativo_id, -quantidade, preco_execucao)

        # Registrar ordem
        cursor.execute("""
            INSERT INTO ordens (id, ativo_id, tipo, preco, quantidade, valor_total, score, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            ordem_id, ativo_id, tipo, preco_execucao,
            quantidade, valor_total, score, "EXECUTADA"
        ))

        # Registrar execução
        cursor.execute("""
            INSERT INTO execucoes (ordem_id, preco_execucao, quantidade, valor_total)
            VALUES (%s,%s,%s,%s)
        """, (
            ordem_id, preco_execucao, quantidade, valor_total
        ))

        # Atualizar capital
        cursor.execute("""
            INSERT INTO capital (capital_total, capital_disponivel, capital_investido)
            VALUES (%s,%s,%s)
        """, (
            capital_total, capital_disp, capital_inv
        ))

    logger.info(f"[BROKER] {tipo} executada | Ativo {ativo_id} | Qtd {quantidade}")

# ============================================================

# PORTFÓLIO

# ============================================================

def obter_portfolio():
    """
    Retorna carteira atual.
    """

    query = """
        SELECT p.ativo_id, a.ticker, p.quantidade, p.preco_medio
        FROM posicoes p
        JOIN ativos a ON a.id = p.ativo_id
    """

    return fetch_dataframe(query)

# ============================================================

# PATRIMÔNIO TOTAL

# ============================================================

def calcular_patrimonio(precos_atualizados: dict):
    """
    Calcula valor total da carteira.
    """

    portfolio = obter_portfolio()

    total = 0

    for _, row in portfolio.iterrows():
        ativo = row["ticker"]
        qtd = row["quantidade"]

        preco = precos_atualizados.get(ativo, 0)

        total += qtd * preco

        capital_total, capital_disp, _ = obter_capital()

        patrimonio = total + capital_disp

        query = """
            INSERT INTO patrimonio (valor_total)
            VALUES (%s)
        """

        execute_query(query, (patrimonio,))

        return patrimonio
