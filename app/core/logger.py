# ============================================================
# LOGGER - SISTEMA DE LOGGING CENTRAL
# ============================================================

import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

from app.core.config import LOG_CONFIG


# ============================================================
# CRIAÇÃO DE DIRETÓRIO
# ============================================================

def _garantir_diretorio(caminho: str):
    pasta = os.path.dirname(caminho)
    if pasta and not os.path.exists(pasta):
        os.makedirs(pasta, exist_ok=True)


# ============================================================
# FORMATTER PADRÃO
# ============================================================

class FormatterPadrao(logging.Formatter):

    def format(self, record):

        tempo = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        mensagem = f"[{tempo}] [{record.levelname}] [{record.name}] {record.getMessage()}"

        if record.exc_info:
            mensagem += f"\n{self.formatException(record.exc_info)}"

        return mensagem


# ============================================================
# CRIAÇÃO DO LOGGER
# ============================================================

def criar_logger(nome: str = "agente_financeiro") -> logging.Logger:

    logger = logging.getLogger(nome)

    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, LOG_CONFIG.nivel.upper(), logging.INFO))

    formatter = FormatterPadrao()

    # =============================
    # CONSOLE
    # =============================

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    # =============================
    # ARQUIVO PRINCIPAL
    # =============================

    log_file = LOG_CONFIG.arquivo
    _garantir_diretorio(log_file)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )

    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    # =============================
    # ARQUIVO DE ERROS
    # =============================

    error_file = log_file.replace(".log", "_error.log")

    error_handler = RotatingFileHandler(
        error_file,
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )

    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    logger.addHandler(error_handler)

    logger.propagate = False

    logger.info(f"[Logger] Logger '{nome}' inicializado")

    return logger


# ============================================================
# LOGGER GLOBAL
# ============================================================

logger = criar_logger()


# ============================================================
# DECORATOR DE LOG
# ============================================================

def logar_execucao(func):

    def wrapper(*args, **kwargs):

        nome_func = func.__name__

        logger.info(f"[EXEC] Iniciando: {nome_func}")

        try:

            resultado = func(*args, **kwargs)

            logger.info(f"[EXEC] Finalizado: {nome_func}")

            return resultado

        except Exception as e:

            logger.error(f"[EXEC] Erro em {nome_func}: {e}", exc_info=True)

            raise

    return wrapper


# ============================================================
# LOG ESTRUTURADO
# ============================================================

def log_estruturado(tipo: str, dados: dict):

    logger.info(f"[EVENTO:{tipo}] {dados}")