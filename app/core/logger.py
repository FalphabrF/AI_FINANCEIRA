# ============================================================

# LOGGER - SISTEMA DE LOGGING CENTRAL

# ============================================================

# Responsável por:

# - Registrar eventos do sistema

# - Permitir auditoria completa

# - Facilitar debug

# - Organizar logs por nível e arquivo

#

# FEATURES:

# - Rotação automática de arquivos

# - Logs separados por nível

# - Formatação padronizada

# - Suporte a múltiplos módulos

# ============================================================

import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

from core.config import LOG_CONFIG

# ============================================================

# CRIAÇÃO DE DIRETÓRIO

# ============================================================

def _garantir_diretorio(caminho: str):
    """
    Garante que o diretório de logs exista.
    """
    pasta = os.path.dirname(caminho)
    if pasta and not os.path.exists(pasta):
        os.makedirs(pasta, exist_ok=True)

# ============================================================

# FORMATAÇÃO PADRÃO

# ============================================================

class FormatterPadrao(logging.Formatter):
    """
    Formatter customizado para logs mais ricos.
    """

    def format(self, record):
        """
        Formata a mensagem de log.
        """

        tempo = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        mensagem = f"[{tempo}] [{record.levelname}] [{record.name}] {record.getMessage()}"

        if record.exc_info:
            mensagem += f"\n{self.formatException(record.exc_info)}"

        return mensagem

    # ============================================================

    # CRIAÇÃO DO LOGGER PRINCIPAL

    # ============================================================

    def criar_logger(nome: str = "agente_financeiro") -> logging.Logger:
        """
        Cria e configura um logger completo.

        ```
        :param nome: nome do logger
        :return: instância de logger configurado
        """

        logger = logging.getLogger(nome)

        # Evita duplicação de handlers
        if logger.handlers:
            return logger

        logger.setLevel(getattr(logging, LOG_CONFIG.nivel.upper(), logging.INFO))

        formatter = FormatterPadrao()

        # ========================================================
        # HANDLER: CONSOLE
        # ========================================================
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

        # ========================================================
        # HANDLER: ARQUIVO (ROTAÇÃO)
        # ========================================================
        log_file = LOG_CONFIG.arquivo
        _garantir_diretorio(log_file)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=5,
            encoding="utf-8"
        )

        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

        # ========================================================
        # HANDLER: ERROS SEPARADOS
        # ========================================================
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

        logger.info(f"[Logger] Logger '{nome}' inicializado com sucesso")

        return logger


    # ============================================================

    # LOGGER GLOBAL

    # ============================================================

    logger = criar_logger()

    # ============================================================

    # DECORATOR DE LOG (OPCIONAL)

    # ============================================================

    def logar_execucao(func):
        """
        Decorator para logar execução de funções automaticamente.
        """

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

    # LOG ESTRUTURADO (AVANÇADO)

    # ============================================================

    def log_estruturado(tipo: str, dados: dict):
        """
        Log estruturado para eventos importantes.

        ```
        :param tipo: tipo do evento (COMPRA, VENDA, ALERTA, etc)
        :param dados: payload do evento
        """

        logger.info(f"[EVENTO:{tipo}] {dados}")

