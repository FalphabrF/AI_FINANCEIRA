# ============================================================

# MAIN - PONTO DE ENTRADA DO SISTEMA

# ============================================================

# Responsável por:

# - Inicializar o sistema

# - Controlar execução (loop / ciclo único)

# - Garantir estabilidade

# - Gerenciar erros globais

#

# MODOS:

# - LOOP: execução contínua

# - ONCE: executa um ciclo

# - DEBUG: execução detalhada

# ============================================================

import time
import signal
import sys

from core.logger import logger
from core.config import EXECUTION_CONFIG

from engine.executor import executar_ciclo

# ============================================================

# CONTROLE DE EXECUÇÃO

# ============================================================

RUNNING = True

def shutdown_handler(signum, frame):
    """
    Captura sinais de encerramento (SIGINT, SIGTERM)
    """
    global RUNNING
    logger.warning("[MAIN] Encerrando sistema...")
    RUNNING = False

    # Registrar sinais do sistema

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

# ============================================================

# MODOS DE EXECUÇÃO

# ============================================================

def executar_loop():
    """
    Loop contínuo do sistema.
    """

    intervalo = EXECUTION_CONFIG.intervalo_segundos

    logger.info(f"[MAIN] Iniciando LOOP | Intervalo: {intervalo}s")

    while RUNNING:
        try:
            inicio = time.time()

            executar_ciclo()

            duracao = time.time() - inicio
            logger.info(f"[MAIN] Ciclo finalizado em {duracao:.2f}s")

        except Exception as e:
            logger.error(f"[MAIN] Erro no ciclo: {e}")

        # Controle de intervalo
        if RUNNING:
            time.sleep(intervalo)

    logger.info("[MAIN] Sistema encerrado com sucesso")

def executar_uma_vez():
    """
    Executa apenas um ciclo.
    """

    logger.info("[MAIN] Executando ciclo único")

    try:
        executar_ciclo()
    except Exception as e:
        logger.error(f"[MAIN] Erro: {e}")

    logger.info("[MAIN] Execução finalizada")

def executar_debug():
    """
    Execução detalhada (debug).
    """

    logger.info("[MAIN] Modo DEBUG ativado")

    try:
        executar_ciclo()
        logger.info("[MAIN] Debug concluído")
    except Exception as e:
        logger.exception("[MAIN] Erro crítico no debug")

# ============================================================

# ENTRYPOINT

# ============================================================

def main():
    """
    Função principal.
    """

    logger.info("========================================")
    logger.info("[MAIN] Inicializando sistema financeiro")
    logger.info("========================================")

    modo = EXECUTION_CONFIG.modo_execucao.upper()

    if modo == "LOOP":
        executar_loop()

    elif modo == "ONCE":
        executar_uma_vez()

    elif modo == "DEBUG":
        executar_debug()

    else:
        logger.error(f"[MAIN] Modo inválido: {modo}")
        sys.exit(1)

# ============================================================

# START

# ============================================================

if __name__ == "__main__":
    main()
