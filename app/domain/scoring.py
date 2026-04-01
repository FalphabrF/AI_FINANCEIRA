# ============================================================

# SCORING - MODELO MULTI-FATOR PROFISSIONAL

# ============================================================

# Responsável por:

# - Avaliar ativos com múltiplos fatores

# - Gerar score quantitativo

# - Definir decisão final (COMPRA / VENDA / HOLD)

#

# FILOSOFIA:

# - Combinação de fundamentos + momentum + risco

# - Evitar decisões baseadas em 1 variável

# - Criar vantagem estatística consistente

# ============================================================

import numpy as np

from app.core.config import SCORING_CONFIG
from app.core.logger import logger

# ============================================================

# CONFIGURAÇÃO

# ============================================================

PESOS = SCORING_CONFIG.pesos
THRESHOLDS = SCORING_CONFIG.thresholds

# ============================================================

# FUNÇÕES AUXILIARES

# ============================================================

def normalizar(valor, minimo, maximo):
    """
    Normaliza valor entre 0 e 1.
    """

    if maximo - minimo == 0:
        return 0

    return max(0, min(1, (valor - minimo) / (maximo - minimo)))

def inverso_normalizado(valor, minimo, maximo):
    """
    Para métricas onde menor é melhor (ex: P/L, volatilidade)
    """

    return 1 - normalizar(valor, minimo, maximo)

# ============================================================

# SCORE FUNDAMENTOS

# ============================================================

def score_fundamentos(dados):
    """
    Avalia qualidade da empresa.
    """

    roe = dados.get("roe", 0)
    pl = dados.get("pl", 0)

    roe_score = normalizar(roe, 0, 0.3)
    pl_score = inverso_normalizado(pl, 5, 30)

    score = (roe_score * 0.6) + (pl_score * 0.4)

    return score * 100

# ============================================================

# SCORE MOMENTO

# ============================================================

def score_momento(dados):
    """
    Avalia tendência e força de preço.
    """

    tendencia = dados.get("tendencia", 0)
    rsi = dados.get("rsi", 50)

    tendencia_score = tendencia  # já 0 ou 1

    # RSI ideal ~ 50-70
    rsi_score = 1 - abs(rsi - 60) / 60

    score = (tendencia_score * 0.7) + (rsi_score * 0.3)

    return max(0, score) * 100

# ============================================================

# SCORE RISCO

# ============================================================

def score_risco(dados):
    """
    Penaliza ativos arriscados.
    """

    volatilidade = dados.get("volatilidade", 0)

    vol_score = inverso_normalizado(volatilidade, 0.1, 0.6)

    return vol_score * 100

# ============================================================

# SCORE LIQUIDEZ

# ============================================================

def score_liquidez(dados):
    """
    Avalia facilidade de entrada/saída.
    """

    volume = dados.get("volume", 0)

    vol_score = normalizar(volume, 1_000_000, 50_000_000)

    return vol_score * 100

# ============================================================

# SCORE QUALIDADE

# ============================================================

def score_qualidade(dados):
    """
    Score complementar.
    """

    # Pode expandir futuramente
    return 50

# ============================================================

# SCORE TOTAL

# ============================================================

def calcular_score_completo(dados):
    """
    Combina todos os fatores.
    """

    fund = score_fundamentos(dados)
    mom = score_momento(dados)
    risco = score_risco(dados)
    liquidez = score_liquidez(dados)
    qualidade = score_qualidade(dados)

    score_total = (
        fund * PESOS["fundamentos"] +
        mom * PESOS["momento"] +
        risco * PESOS["risco"] +
        liquidez * PESOS["liquidez"] +
        qualidade * PESOS["qualidade"]
    )

    resultado = {
        "score_total": score_total,
        "fundamentos": fund,
        "momento": mom,
        "risco": risco,
        "liquidez": liquidez,
        "qualidade": qualidade
    }

    return resultado

# ============================================================

# DECISÃO FINAL

# ============================================================

def gerar_decisao(score):
    """
    Converte score em ação.
    """

    if score >= THRESHOLDS["compra"]:
        return "COMPRA"

    elif score <= THRESHOLDS["venda"]:
        return "VENDA"

    return "HOLD"

# ============================================================

# DEBUG / LOG

# ============================================================

def logar_score(ativo, score_data, decisao):
    """
    Log detalhado para análise.
    """

    logger.info(
        f"[SCORING] {ativo} | "
        f"Total: {score_data['score_total']:.2f} | "
        f"F:{score_data['fundamentos']:.1f} "
        f"M:{score_data['momento']:.1f} "
        f"R:{score_data['risco']:.1f} "
        f"L:{score_data['liquidez']:.1f} | "
        f"{decisao}"
    )
