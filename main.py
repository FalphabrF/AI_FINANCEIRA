# ============================================================
# MAIN - PONTO DE ENTRADA DO SISTEMA
# ============================================================

import time
import signal
import sys

from app.core.config import CONFIG
from app.core.logger import logger

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


# Registrar sinais corretamente
signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)


# ============================================================
# CICLO PRINCIPAL (placeholder)
# ============================================================

def executar_ciclo():
    """
    Ciclo principal do sistema.
    Aqui futuramente rodará:
    - coleta de dados
    - análise
    - decisão de trade
    - registro no banco
    """

    logger.info("[CICLO] Executando ciclo do sistema")

    # Placeholder temporário
    time.sleep(2)

    logger.info("[CICLO] Ciclo concluído")


# ============================================================
# MODOS DE EXECUÇÃO
# ============================================================

def executar_loop():
    """
    Loop contínuo do sistema.
    """

    intervalo = getattr(CONFIG, "intervalo_segundos", 3600)

    logger.info(f"[MAIN] Iniciando LOOP | Intervalo: {intervalo}s")

    while RUNNING:

        try:
            inicio = time.time()

            executar_ciclo()

            duracao = time.time() - inicio
            logger.info(f"[MAIN] Ciclo finalizado em {duracao:.2f}s")

        except Exception as e:
            logger.error(f"[MAIN] Erro no ciclo: {e}", exc_info=True)

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
        logger.error(f"[MAIN] Erro: {e}", exc_info=True)

    logger.info("[MAIN] Execução finalizada")


def executar_debug():
    """
    Execução detalhada (debug).
    """

    logger.info("[MAIN] Modo DEBUG ativado")

    try:
        executar_ciclo()

    except Exception:
        logger.exception("[MAIN] Erro crítico no debug")

    logger.info("[MAIN] Debug concluído")


# ============================================================
# ENTRYPOINT
# ============================================================

def main():
    """
    Função principal do sistema.
    """

    logger.info("========================================")
    logger.info("[MAIN] Inicializando sistema financeiro")
    logger.info("========================================")

    # valor padrão caso não exista na config
    modo = getattr(CONFIG, "modo_execucao", "LOOP").upper()

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