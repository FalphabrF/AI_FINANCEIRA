# ============================================================

# ENGINE - ORQUESTRADOR CENTRAL DO SISTEMA

# ============================================================

# Responsável por:

# - Coordenar todos os agentes

# - Executar o fluxo completo do sistema

# - Integrar dados, decisão e execução

# - Garantir consistência do ciclo operacional

#

# FLUXO:

# 1. Coleta de dados

# 2. Atualização do estado financeiro

# 3. Análise de compra

# 4. Análise de venda

# 5. Solicitação de aprovação (n8n)

# 6. Execução das operações

# 7. Registro e persistência

#

# IMPORTANTE:

# Este é o "cérebro operacional" do sistema.

# ============================================================

import time
from typing import List, Dict

from core.logger import logger

# Agentes

from agents.agente_compra import AgenteCompra
from agents.agente_venda import AgenteVenda
from agents.agente_financeiro import AgenteFinanceiro

# Integrações

from integrations.n8n_hooks import N8NHooks

# Dados

from data.coleta_dados import pegar_dados_reais
from data.posicoes import obter_posicoes_abertas

class Engine:
    """
    Orquestrador principal do sistema.
    """

def __init__(self):
    logger.info("[Engine] Inicializando sistema...")

    # Inicialização de agentes
    self.financeiro = AgenteFinanceiro()
    estado = self.financeiro.obter_estado_financeiro()

    self.agente_compra = AgenteCompra(
        capital_total=estado["capital_total"],
        capital_disponivel=estado["capital_disponivel"]
    )

    self.agente_venda = AgenteVenda()

    # Integração externa
    self.n8n = N8NHooks()

    logger.info("[Engine] Sistema inicializado com sucesso")

# ============================================================
# CICLO COMPLETO
# ============================================================
def executar_ciclo(self):
    """
    Executa um ciclo completo do sistema.
    """

    logger.info("[Engine] Iniciando ciclo operacional")

    try:
        # ====================================================
        # 1. COLETA DE DADOS
        # ====================================================
        dados_ativos = pegar_dados_reais()

        if dados_ativos is None or dados_ativos.empty:
            logger.warning("[Engine] Nenhum dado disponível para análise")
            return

        lista_ativos = dados_ativos.to_dict("records")

        # ====================================================
        # 2. ATUALIZAÇÃO FINANCEIRA
        # ====================================================
        estado = self.financeiro.obter_estado_financeiro()

        # ====================================================
        # 3. ANÁLISE DE COMPRA
        # ====================================================
        oportunidades = self.agente_compra.analisar_ativos(lista_ativos)

        for decisao in oportunidades:
            resposta = self.n8n.solicitar_aprovacao_compra(decisao)
            aprovado = self.n8n.interpretar_resposta(resposta)

            if aprovado:
                self.agente_compra.executar_compra(decisao, True)
                self.financeiro.registrar_compra(decisao["valor_total"])

        # ====================================================
        # 4. ANÁLISE DE VENDA
        # ====================================================
        posicoes = obter_posicoes_abertas()

        if posicoes:
            decisoes_venda = self.agente_venda.analisar_posicoes(posicoes)

            for decisao in decisoes_venda:
                resposta = self.n8n.solicitar_aprovacao_venda(decisao)
                aprovado = self.n8n.interpretar_resposta(resposta)

                if aprovado:
                    self.agente_venda.executar_venda(decisao, True)

                    valor_venda = decisao["quantidade"] * decisao["preco_venda"]
                    lucro = valor_venda - (decisao["quantidade"] * decisao["preco_compra"])

                    self.financeiro.registrar_venda(valor_venda, lucro)

        # ====================================================
        # 5. SNAPSHOT FINANCEIRO
        # ====================================================
        self.financeiro.registrar_snapshot()

        logger.info("[Engine] Ciclo finalizado com sucesso")

    except Exception as e:
        logger.error(f"[Engine] Erro crítico no ciclo: {e}")

# ============================================================
# LOOP CONTÍNUO
# ============================================================
def iniciar_loop(self, intervalo_segundos: int = 3600):
    """
    Inicia execução contínua do sistema.

    :param intervalo_segundos: tempo entre ciclos
    """

    logger.info(f"[Engine] Iniciando loop contínuo | Intervalo: {intervalo_segundos}s")

    while True:
        self.executar_ciclo()

        logger.info(f"[Engine] Aguardando {intervalo_segundos} segundos para próximo ciclo")

        time.sleep(intervalo_segundos)

