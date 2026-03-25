# ============================================================

# METRICS - ANÁLISE DE PERFORMANCE DO SISTEMA

# ============================================================

# Responsável por:

# - Calcular métricas financeiras

# - Avaliar risco e retorno

# - Medir qualidade da estratégia

# - Gerar insights quantitativos

#

# UTILIZAÇÃO:

# - Backtests

# - Monitoramento em produção

# - Comparação de estratégias

# ============================================================

import numpy as np
import pandas as pd
from typing import Dict

class Metrics:
    """
    Classe responsável por calcular métricas financeiras avançadas.
    """

def __init__(self, df: pd.DataFrame):
    """
    :param df: DataFrame com coluna 'patrimonio'
    """
    if df is None or df.empty:
        raise ValueError("DataFrame inválido para métricas")

    if "patrimonio" not in df.columns:
        raise ValueError("DataFrame deve conter coluna 'patrimonio'")

    self.df = df.copy()

    # Retornos percentuais
    self.df["retorno"] = self.df["patrimonio"].pct_change()

    # Remove NaNs iniciais
    self.df = self.df.dropna()

# ============================================================
# RETORNO
# ============================================================
def retorno_total(self) -> float:
    """
    Retorno total da estratégia.
    """
    inicial = self.df["patrimonio"].iloc[0]
    final = self.df["patrimonio"].iloc[-1]

    return (final / inicial) - 1

def retorno_anualizado(self) -> float:
    """
    Retorno anualizado (CAGR).
    """
    dias = len(self.df)

    retorno_total = self.retorno_total()

    return (1 + retorno_total) ** (252 / dias) - 1

# ============================================================
# RISCO
# ============================================================
def volatilidade_anualizada(self) -> float:
    """
    Volatilidade anualizada.
    """
    return self.df["retorno"].std() * np.sqrt(252)

def max_drawdown(self) -> float:
    """
    Máximo drawdown da curva de patrimônio.
    """
    patrimonio = self.df["patrimonio"]
    pico = patrimonio.cummax()
    drawdown = (patrimonio / pico) - 1

    return drawdown.min()

# ============================================================
# RISCO AJUSTADO
# ============================================================
def sharpe_ratio(self, risk_free_rate: float = 0.0) -> float:
    """
    Sharpe Ratio.

    :param risk_free_rate: taxa livre de risco anual
    """
    retorno_medio = self.df["retorno"].mean() * 252
    volatilidade = self.volatilidade_anualizada()

    if volatilidade == 0:
        return 0

    return (retorno_medio - risk_free_rate) / volatilidade

def sortino_ratio(self, risk_free_rate: float = 0.0) -> float:
    """
    Sortino Ratio (penaliza apenas downside).
    """
    downside = self.df[self.df["retorno"] < 0]["retorno"]

    if downside.empty:
        return 0

    downside_std = downside.std() * np.sqrt(252)

    retorno_medio = self.df["retorno"].mean() * 252

    return (retorno_medio - risk_free_rate) / downside_std

# ============================================================
# CONSISTÊNCIA
# ============================================================
def win_rate(self) -> float:
    """
    Percentual de períodos positivos.
    """
    positivos = (self.df["retorno"] > 0).sum()
    total = len(self.df)

    return positivos / total

def profit_factor(self) -> float:
    """
    Relação entre ganhos e perdas.
    """
    ganhos = self.df[self.df["retorno"] > 0]["retorno"].sum()
    perdas = abs(self.df[self.df["retorno"] < 0]["retorno"].sum())

    if perdas == 0:
        return np.inf

    return ganhos / perdas

# ============================================================
# EFICIÊNCIA
# ============================================================
def expectativa(self) -> float:
    """
    Expectativa matemática da estratégia.
    """
    ganhos = self.df[self.df["retorno"] > 0]["retorno"]
    perdas = self.df[self.df["retorno"] < 0]["retorno"]

    if ganhos.empty or perdas.empty:
        return 0

    win_rate = len(ganhos) / len(self.df)
    loss_rate = 1 - win_rate

    media_ganho = ganhos.mean()
    media_perda = perdas.mean()

    return (win_rate * media_ganho) + (loss_rate * media_perda)

# ============================================================
# RESUMO COMPLETO
# ============================================================
def resumo(self) -> Dict:
    """
    Retorna todas as métricas principais.
    """

    return {
        "retorno_total_%": self.retorno_total() * 100,
        "retorno_anual_%": self.retorno_anualizado() * 100,
        "volatilidade_%": self.volatilidade_anualizada() * 100,
        "max_drawdown_%": self.max_drawdown() * 100,
        "sharpe": self.sharpe_ratio(),
        "sortino": self.sortino_ratio(),
        "win_rate_%": self.win_rate() * 100,
        "profit_factor": self.profit_factor(),
        "expectativa": self.expectativa()
    }
