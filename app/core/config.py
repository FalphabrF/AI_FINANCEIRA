# ============================================================

# CONFIG - CONFIGURAÇÕES CENTRAIS DO SISTEMA

# ============================================================

# Responsável por:

# - Centralizar todas as configurações

# - Permitir fácil ajuste de parâmetros

# - Separar ambiente (dev/prod)

# - Evitar hardcode no sistema

#

# IMPORTANTE:

# NUNCA colocar dados sensíveis diretamente no código.

# Use variáveis de ambiente (.env).

# ============================================================

import os
from dataclasses import dataclass

# ============================================================

# FUNÇÃO AUXILIAR

# ============================================================

def get_env(key: str, default=None, cast_type=None):
    """
    Obtém variável de ambiente com suporte a tipo.

    ```
    :param key: nome da variável
    :param default: valor padrão
    :param cast_type: tipo desejado (int, float, bool, etc)
    """

    value = os.getenv(key, default)

    if value is None:
        return None

    if cast_type:
        try:
            if cast_type == bool:
                return str(value).lower() in ["true", "1", "yes"]
            return cast_type(value)
        except Exception:
            raise ValueError(f"Erro ao converter variável {key}")

    return value


# ============================================================

# AMBIENTE

# ============================================================

ENV = get_env("ENV", "development")

DEBUG = get_env("DEBUG", True, bool)

# ============================================================

# BANCO DE DADOS

# ============================================================

@dataclass
class DatabaseConfig:
    host: str = get_env("DB_HOST", "localhost")
    port: int = get_env("DB_PORT", 5432, int)
    name: str = get_env("DB_NAME", "agente_financeiro")
    user: str = get_env("DB_USER", "postgres")
    password: str = get_env("DB_PASS", "postgres")

    DB_CONFIG = DatabaseConfig()

# ============================================================

# API / EXTERNOS

# ============================================================

@dataclass
class APIConfig:
    corretora_url: str = get_env("API_CORRETORA", "")
    timeout: int = get_env("API_TIMEOUT", 10, int)

    API_CONFIG = APIConfig()

# ============================================================

# N8N / AUTOMAÇÃO

# ============================================================

@dataclass
class N8NConfig:
    webhook_url: str = get_env("N8N_WEBHOOK_URL", "http://n8n:5678/webhook/agente")
    timeout: int = get_env("N8N_TIMEOUT", 10, int)

    N8N_CONFIG = N8NConfig()

# ============================================================

# CAPITAL

# ============================================================

@dataclass
class CapitalConfig:
    capital_inicial: float = get_env("CAPITAL_INICIAL", 10000, float)
    percentual_alocacao: float = get_env("PCT_ALOCACAO", 0.5, float)

    CAPITAL_CONFIG = CapitalConfig()

# ============================================================

# RISCO

# ============================================================

@dataclass
class RiskConfig:
    stop_loss: float = get_env("STOP_LOSS", 0.15, float)
    take_profit: float = get_env("TAKE_PROFIT", 0.25, float)
    max_exposicao_por_ativo: float = get_env("MAX_EXPOSICAO_ATIVO", 0.2, float)
    max_exposicao_total: float = get_env("MAX_EXPOSICAO_TOTAL", 0.7, float)

    RISK_CONFIG = RiskConfig()

# ============================================================

# MODELO (SCORING)

# ============================================================

@dataclass
class ModelConfig:
    score_minimo_compra: float = get_env("SCORE_MINIMO_COMPRA", 60, float)


# Pesos principais (podem evoluir depois)
    peso_fundamentos: float = get_env("PESO_FUNDAMENTOS", 0.4, float)
    peso_momento: float = get_env("PESO_MOMENTO", 0.3, float)
    peso_risco: float = get_env("PESO_RISCO", 0.2, float)
    peso_liquidez: float = get_env("PESO_LIQUIDEZ", 0.1, float)


    MODEL_CONFIG = ModelConfig()

# ============================================================

# ENGINE

# ============================================================

@dataclass
class EngineConfig:
    intervalo_execucao: int = get_env("INTERVALO_EXECUCAO", 3600, int)

    ENGINE_CONFIG = EngineConfig()

# ============================================================

# LOGGING

# ============================================================

@dataclass
class LoggingConfig:
    nivel: str = get_env("LOG_LEVEL", "INFO")
    arquivo: str = get_env("LOG_FILE", "data/logs/execucao.log")

    LOG_CONFIG = LoggingConfig()

# ============================================================

# VALIDAÇÃO FINAL

# ============================================================

def validar_config():
    """
    Valida configurações críticas do sistema.
    """

if MODEL_CONFIG.score_minimo_compra <= 0:
    raise ValueError("Score mínimo inválido")

if RISK_CONFIG.stop_loss <= 0 or RISK_CONFIG.stop_loss >= 1:
    raise ValueError("Stop loss inválido")

if CAPITAL_CONFIG.percentual_alocacao <= 0 or CAPITAL_CONFIG.percentual_alocacao > 1:
    raise ValueError("Percentual de alocação inválido")

if ENGINE_CONFIG.intervalo_execucao <= 0:
    raise ValueError("Intervalo de execução inválido")

# Executa validação ao importar

validar_config()
