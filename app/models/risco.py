# ============================================================

# RISCO - CONTROLE AVANÇADO DE RISCO

# ============================================================

# Responsável por:

# - Controle de perda máxima

# - Validação de trades

# - Gestão de drawdown

# - Proteção do portfólio

#

# PRINCÍPIOS:

# - Nunca arriscar mais do que pode perder

# - Sobrevivência > Lucro

# ============================================================

import numpy as np
import pandas as pd

from core.logger import logger
from core.config import RISK_CONFIG
from execution.broker_simulado import obter_portfolio, calcular_patrimonio

# ============================================================

# CONFIG

# ============================================================

MAX_RISCO_POR_TRADE = RISK_CONFIG.max_risco_por_trade        # ex: 0.02
MAX_DRAWDOWN = RISK_CONFIG.max_drawdown                      # ex: 0.20
MAX_EXPOSICAO_ATIVO = RISK_CONFIG.max_exposicao_ativo        # ex: 0.25

# ============================================================

# CALCULAR TAMANHO DA POSIÇÃO

# ============================================================

def calcular_position_size(capital_total: float, preco: float, stop_loss: float):
    """
    Define quanto comprar baseado no risco.
    """

    risco_por_trade = capital_total * MAX_RISCO_POR_TRADE

    risco_por_acao = abs(preco - stop_loss)

    if risco_por_acao <= 0:
        return 0

    quantidade = int(risco_por_trade / risco_por_acao)

    return max(0, quantidade)

# ============================================================

# STOP LOSS DINÂMICO

# ============================================================

def calcular_stop_loss(preco: float, volatilidade: float):
    """
    Stop baseado na volatilidade.
    """

    fator = 2  # multiplicador

    stop = preco - (volatilidade * fator * preco)

    return max(stop, preco * 0.85)  # limite mínimo

# ============================================================

# VERIFICAR EXPOSIÇÃO

# ============================================================

def verificar_exposicao(ativo: str, capital_total: float, preco: float, quantidade: int):
    """
    Evita concentração excessiva.
    """

    portfolio = obter_portfolio()

    valor_novo = preco * quantidade

    valor_atual = 0

    if not portfolio.empty:
        linha = portfolio[portfolio["ticker"] == ativo]

        if not linha.empty:
            valor_atual = linha["quantidade"].iloc[0] * preco

    exposicao_total = (valor_atual + valor_novo) / capital_total

    if exposicao_total > MAX_EXPOSICAO_ATIVO:
        logger.warning(f"[RISCO] Exposição alta em {ativo}")
        return False

    return True

# ============================================================

# VERIFICAR DRAWDOWN

# ============================================================

def verificar_drawdown(historico_patrimonio: pd.DataFrame):
    """
    Bloqueia operações se drawdown for alto.
    """

    if historico_patrimonio.empty:
        return True

    df = historico_patrimonio.copy()

    df["pico"] = df["valor_total"].cummax()
    df["drawdown"] = (df["valor_total"] / df["pico"]) - 1

    drawdown_atual = df["drawdown"].iloc[-1]

    if drawdown_atual <= -MAX_DRAWDOWN:
        logger.error("[RISCO] Drawdown máximo atingido - operações bloqueadas")
        return False

    return True

# ============================================================

# VALIDAR ORDEM

# ============================================================

def validar_ordem(
    ativo: str,
    preco: float,
    volatilidade: float,
    capital_total: float,
    historico_patrimonio: pd.DataFrame
    ):
    """
    Validação completa antes da execução.
    """

    # 1. Verificar drawdown
    if not verificar_drawdown(historico_patrimonio):
        return {"permitido": False, "motivo": "DRAWNDOWN_EXCEDIDO"}

    # 2. Calcular stop
    stop = calcular_stop_loss(preco, volatilidade)

    # 3. Calcular posição
    quantidade = calcular_position_size(capital_total, preco, stop)

    if quantidade <= 0:
        return {"permitido": False, "motivo": "POSICAO_INVALIDA"}

    # 4. Verificar exposição
    if not verificar_exposicao(ativo, capital_total, preco, quantidade):
        return {"permitido": False, "motivo": "EXPOSICAO_ALTA"}

    return {
        "permitido": True,
        "quantidade": quantidade,
        "stop_loss": stop
    }

# ============================================================

# CONTROLE DE OVERTRADING

# ============================================================

def verificar_overtrading(trades_df: pd.DataFrame):
    """
    Evita operações excessivas.
    """

    if trades_df.empty:
        return True

    trades_recentes = trades_df.tail(10)

    perdas = (trades_recentes["lucro"] < 0).sum()

    if perdas >= 7:
        logger.warning("[RISCO] Muitas perdas recentes - pausa recomendada")
        return False

    return True

# ============================================================

# RISCO TOTAL DO PORTFÓLIO

# ============================================================

def calcular_risco_portfolio():
    """
    Mede risco geral da carteira.
    """

    portfolio = obter_portfolio()

    if portfolio.empty:
        return 0

    # Simples: concentração
    valores = portfolio["quantidade"] * portfolio["preco"]

    total = valores.sum()

    pesos = valores / total

    risco = np.sum(pesos ** 2)  # concentração

    return risco

# ============================================================

# PROTEÇÃO GLOBAL

# ============================================================

def sistema_em_risco(historico_patrimonio: pd.DataFrame):
    """
    Avaliação geral do sistema.
    """

    if not verificar_drawdown(historico_patrimonio):
        return True

    risco_portfolio = calcular_risco_portfolio()

    if risco_portfolio > 0.3:
        logger.warning("[RISCO] Carteira muito concentrada")
        return True

    return False
