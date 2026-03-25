# ============================================================

# PORTFOLIO - GESTÃO DE CARTEIRA E ALOCAÇÃO DE CAPITAL

# ============================================================

# Responsável por:

# - Definir quanto investir em cada ativo

# - Controlar risco e exposição

# - Gerenciar diversificação

# - Rebalancear carteira

#

# ESTRATÉGIA:

# - Score-based allocation

# - Risk-adjusted weights

# - Limite por ativo

# ============================================================

import pandas as pd
import numpy as np

from core.logger import logger
from core.config import PORTFOLIO_CONFIG

from execution.broker_simulado import obter_portfolio

# ============================================================

# CONFIG PADRÃO

# ============================================================

MAX_PESO_ATIVO = PORTFOLIO_CONFIG.max_peso_ativo      # ex: 0.2
MIN_SCORE = PORTFOLIO_CONFIG.min_score                # ex: 60
MAX_ATIVOS = PORTFOLIO_CONFIG.max_ativos              # ex: 10

# ============================================================

# FILTRAR ATIVOS

# ============================================================

def filtrar_ativos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filtra ativos com base no score mínimo.
    """

    df = df.copy()

    df = df[df["score_total"] >= MIN_SCORE]

    if df.empty:
        logger.warning("[PORTFOLIO] Nenhum ativo passou no filtro")
        return df

    # Ordena por score
    df = df.sort_values(by="score_total", ascending=False)

    # Limita quantidade
    df = df.head(MAX_ATIVOS)

    return df

# ============================================================

# CALCULAR PESOS

# ============================================================

def calcular_pesos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Define peso de cada ativo na carteira.
    """

    df = df.copy()

    # Peso proporcional ao score
    soma_scores = df["score_total"].sum()

    if soma_scores == 0:
        df["peso"] = 0
        return df

    df["peso"] = df["score_total"] / soma_scores

    # Limitar peso máximo
    df["peso"] = df["peso"].apply(lambda x: min(x, MAX_PESO_ATIVO))

    # Renormalizar
    df["peso"] = df["peso"] / df["peso"].sum()

    return df

# ============================================================

# AJUSTE POR RISCO

# ============================================================

def ajustar_por_risco(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reduz peso de ativos mais voláteis.
    """

    df = df.copy()

    if "volatilidade" not in df.columns:
        return df

    # Inverso da volatilidade
    df["peso_risco"] = 1 / (df["volatilidade"] + 1e-6)

    df["peso_risco"] = df["peso_risco"] / df["peso_risco"].sum()

    # Combinar com peso original
    df["peso_final"] = (df["peso"] + df["peso_risco"]) / 2

    # Normalizar
    df["peso_final"] = df["peso_final"] / df["peso_final"].sum()

    return df

# ============================================================

# GERAR ALOCAÇÃO

# ============================================================

def gerar_alocacao(df_scores: pd.DataFrame, capital_total: float) -> pd.DataFrame:
    """
    Gera plano de alocação.
    """

    logger.info("[PORTFOLIO] Gerando alocação")

    df = filtrar_ativos(df_scores)

    if df.empty:
        return df

    df = calcular_pesos(df)
    df = ajustar_por_risco(df)

    df["capital_alocado"] = df["peso_final"] * capital_total

    return df

# ============================================================

# REBALANCEAMENTO

# ============================================================

def calcular_rebalanceamento(df_alocacao: pd.DataFrame):
    """
    Compara carteira atual com ideal.
    """

    portfolio_atual = obter_portfolio()

    if portfolio_atual.empty:
        logger.info("[PORTFOLIO] Carteira vazia - sem rebalanceamento")
        return df_alocacao

    # Merge com carteira atual
    df = df_alocacao.merge(
        portfolio_atual,
        left_on="ativo",
        right_on="ticker",
        how="left"
    )

    df["quantidade"] = df["quantidade"].fillna(0)

    # Calcular diferença (simplificado)
    df["ajuste"] = df["capital_alocado"] - (df["quantidade"] * df["preco"])

    return df

# ============================================================

# GERAR ORDENS

# ============================================================

def gerar_ordens(df_rebalanceado: pd.DataFrame):
    """
    Cria lista de ordens (compra/venda).
    """

    ordens = []

    for _, row in df_rebalanceado.iterrows():

        ajuste = row["ajuste"]
        preco = row["preco"]

        if preco <= 0:
            continue

        quantidade = int(abs(ajuste) // preco)

        if quantidade == 0:
            continue

        tipo = "COMPRA" if ajuste > 0 else "VENDA"

        ordens.append({
            "ativo": row["ativo"],
            "tipo": tipo,
            "quantidade": quantidade,
            "preco": preco
        })

    return ordens

# ============================================================

# PIPELINE COMPLETO

# ============================================================

def executar_gestao_portfolio(df_scores: pd.DataFrame, capital_total: float):
    """
    Pipeline completo:
    - Seleção
    - Alocação
    - Rebalanceamento
    - Geração de ordens
    """

    logger.info("[PORTFOLIO] Iniciando gestão")

    df_alocacao = gerar_alocacao(df_scores, capital_total)

    if df_alocacao.empty:
        return []

    df_rebalanceado = calcular_rebalanceamento(df_alocacao)

    ordens = gerar_ordens(df_rebalanceado)

    logger.info(f"[PORTFOLIO] {len(ordens)} ordens geradas")

    return ordens
