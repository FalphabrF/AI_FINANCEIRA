# ============================================================

# UTILS - FUNÇÕES UTILITÁRIAS DO SISTEMA

# ============================================================

# Responsável por:

# - Reutilização de código

# - Abstração de operações comuns

# - Padronização de comportamento

# - Redução de duplicação

#

# INCLUI:

# - Banco de dados (PostgreSQL)

# - Retry automático

# - Funções financeiras

# - Manipulação de dados

# ============================================================

import time
import psycopg2
import pandas as pd
from functools import wraps
from typing import Callable, Any, Dict

from app.core.config import DB_CONFIG
from app.core.logger import logger

# ============================================================

# RETRY DECORATOR

# ============================================================

def retry(max_tentativas: int = 3, delay: int = 2):
    """
    Decorator para retry automático em caso de falha.
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):

            for tentativa in range(1, max_tentativas + 1):
                try:
                    return func(*args, **kwargs)

                except Exception as e:
                    logger.warning(
                        f"[Retry] Tentativa {tentativa}/{max_tentativas} falhou em {func.__name__}: {e}"
                    )

                    if tentativa == max_tentativas:
                        logger.error(f"[Retry] Falha definitiva em {func.__name__}")
                        raise

                    time.sleep(delay)

        return wrapper

    return decorator

# ============================================================

# CONEXÃO COM BANCO

# ============================================================

@retry(max_tentativas=5, delay=3)
def get_connection():
    """
    Cria conexão com PostgreSQL com retry automático.
    """
    
    conn = psycopg2.connect(
        host=DB_CONFIG.host,
        port=DB_CONFIG.port,
        database=DB_CONFIG.name,
        user=DB_CONFIG.user,
        password=DB_CONFIG.password
    )

    return conn


def executar_query(query: str, params: tuple = None, fetch: bool = False):
    """
    Executa query no banco.

    :param query: SQL
    :param params: parâmetros
    :param fetch: retorna resultados
    """

    conn = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(query, params or ())

        if fetch:
            resultado = cursor.fetchall()
            return resultado

        conn.commit()

    except Exception as e:
        logger.error(f"[DB] Erro ao executar query: {e}")
        raise

    finally:
        if conn:
            conn.close()

def query_to_dataframe(query: str) -> pd.DataFrame:
    """
    Executa query e retorna DataFrame.
    """

    conn = get_connection()

    try:
        df = pd.read_sql(query, conn)
        return df

    except Exception as e:
        logger.error(f"[DB] Erro ao converter query para DataFrame: {e}")
        raise

    finally:
        conn.close()

# ============================================================

# UTILITÁRIOS FINANCEIROS

# ============================================================

def calcular_retorno(preco_compra: float, preco_venda: float) -> float:
    """
    Calcula retorno percentual.
    """
    if preco_compra == 0:
        return 0

    return (preco_venda / preco_compra) - 1

def calcular_valor_total(preco: float, quantidade: int) -> float:
    """
    Calcula valor total de uma operação.
    """
    return preco * quantidade

def calcular_quantidade(capital: float, preco: float) -> int:
    """
    Calcula quantidade de ativos possível comprar.
    """
    if preco <= 0:
     return 0    

    return int(capital // preco)

# ============================================================

# NORMALIZAÇÃO DE DADOS

# ============================================================

def normalizar_score(valor: float, minimo: float, maximo: float) -> float:
    """
    Normaliza valor entre 0 e 1.
    """

    if maximo == minimo:
        return 0

    return (valor - minimo) / (maximo - minimo)

def limitar(valor: float, minimo: float, maximo: float) -> float:
    """
    Limita valor dentro de um range.
    """
    return max(min(valor, maximo), minimo)

# ============================================================

# VALIDAÇÕES

# ============================================================

def validar_numero(valor: Any, default: float = 0.0) -> float:
    """
    Garante que valor seja numérico.
    """

    try:
        return float(valor)
    except (ValueError, TypeError):
        return default

def validar_dataframe(df: pd.DataFrame) -> bool:
    """
    Verifica se DataFrame é válido.
    """
    return df is not None and not df.empty

# ============================================================

# LOGGING AUXILIAR

# ============================================================

def log_operacao(tipo: str, dados: Dict):
    """
    Log estruturado de operação financeira.
    """

    logger.info(f"[OPERACAO:{tipo}] {dados}")

# ============================================================

# TEMPO / CONTROLE

# ============================================================

def timestamp_atual():
    """
    Retorna timestamp atual.
    """
    return int(time.time())

def sleep_seguro(segundos: int):
    """
    Sleep com log.
    """
    logger.info(f"[SLEEP] Aguardando {segundos}s")
    time.sleep(segundos)
