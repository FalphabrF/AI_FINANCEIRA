# ============================================================
# CONNECTION - GERENCIAMENTO DE BANCO DE DADOS
# ============================================================

import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
import time

from app.core.config import DB_CONFIG
from app.core.logger import logger


# ============================================================
# CONFIGURAÇÃO DO POOL
# ============================================================

class DatabasePool:
    """
    Gerenciador de pool de conexões PostgreSQL.
    """

    def __init__(self):
        self._pool = None

    def inicializar(self, minconn: int = 1, maxconn: int = 10):
        """
        Inicializa o pool de conexões.
        """

        if self._pool:
            return

        try:
            self._pool = psycopg2.pool.SimpleConnectionPool(
                minconn,
                maxconn,
                host=DB_CONFIG.host,
                port=DB_CONFIG.port,
                database=DB_CONFIG.name,
                user=DB_CONFIG.user,
                password=DB_CONFIG.password
            )

            logger.info("[DB] Pool de conexões inicializado")

        except Exception as e:
            logger.error(f"[DB] Erro ao criar pool: {e}")
            raise

    def obter_conexao(self):
        """
        Obtém conexão do pool.
        """

        if not self._pool:
            self.inicializar()

        try:
            return self._pool.getconn()

        except Exception as e:
            logger.error(f"[DB] Erro ao obter conexão: {e}")
            raise

    def devolver_conexao(self, conn):
        """
        Retorna conexão ao pool.
        """

        if self._pool and conn:
            self._pool.putconn(conn)

    def fechar_tudo(self):
        """
        Fecha todas as conexões do pool.
        """

        if self._pool:
            self._pool.closeall()
            logger.info("[DB] Pool encerrado")


# ============================================================
# INSTÂNCIA GLOBAL DO POOL
# ============================================================

db_pool = DatabasePool()


# ============================================================
# RETRY DECORATOR
# ============================================================

def retry(max_tentativas=3, delay=2):
    """
    Retry automático para operações críticas.
    """

    def decorator(func):

        def wrapper(*args, **kwargs):

            for tentativa in range(1, max_tentativas + 1):

                try:
                    return func(*args, **kwargs)

                except Exception as e:

                    logger.warning(
                        f"[DB] Tentativa {tentativa} falhou: {e}"
                    )

                    if tentativa == max_tentativas:
                        logger.error("[DB] Falha definitiva")
                        raise

                    time.sleep(delay)

        return wrapper

    return decorator


# ============================================================
# CONTEXT MANAGER DE CONEXÃO
# ============================================================

@contextmanager
def get_db_connection():
    """
    Context manager para uso seguro da conexão.
    """

    conn = None

    try:
        conn = db_pool.obter_conexao()
        yield conn

    except Exception as e:
        logger.error(f"[DB] Erro na conexão: {e}")
        raise

    finally:
        if conn:
            db_pool.devolver_conexao(conn)


# ============================================================
# EXECUÇÃO DE QUERY
# ============================================================

@retry(max_tentativas=3)
def execute_query(query: str, params: tuple = None, fetch: bool = False):
    """
    Executa query no banco com segurança.
    """

    with get_db_connection() as conn:

        cursor = conn.cursor()

        try:
            cursor.execute(query, params or ())

            if fetch:
                result = cursor.fetchall()
                return result

            conn.commit()

        except Exception as e:

            conn.rollback()
            logger.error(f"[DB] Erro na query: {e}")
            raise

        finally:
            cursor.close()


# ============================================================
# FETCH COMO DATAFRAME
# ============================================================

def fetch_dataframe(query: str):
    """
    Retorna resultado como DataFrame.
    """

    import pandas as pd

    with get_db_connection() as conn:

        try:
            df = pd.read_sql(query, conn)
            return df

        except Exception as e:
            logger.error(f"[DB] Erro ao converter para DataFrame: {e}")
            raise


# ============================================================
# TRANSAÇÕES MANUAIS
# ============================================================

@contextmanager
def transacao():
    """
    Permite múltiplas operações atômicas.
    """

    with get_db_connection() as conn:

        cursor = conn.cursor()

        try:
            yield cursor
            conn.commit()

        except Exception as e:

            conn.rollback()
            logger.error(f"[DB] Transação falhou: {e}")
            raise

        finally:
            cursor.close()