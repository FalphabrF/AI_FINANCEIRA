# ============================================================
# AGENTE DE VENDA
# ============================================================
# Responsável por:
# - Monitorar posições abertas
# - Reavaliar ativos com base no modelo
# - Identificar sinais de venda
# - Proteger capital (stop / risco)
# - Realizar lucro de forma estratégica
#
# IMPORTANTE:
# Este agente NÃO executa vendas automaticamente.
# Ele gera decisões que devem ser aprovadas.
# ============================================================

from typing import List, Dict
from datetime import datetime

from app.core.logger import logger
from app.domain.scoring import calcular_score_completo
from app.domain.risco import validar_venda
from app.execution.executor import registrar_ordem


class AgenteVenda:

    """
    Responsável por analisar posições abertas e decidir quando vender.
    """

    def __init__(self):

        logger.info("[AgenteVenda] Inicializado")

    # ============================================================
    # MÉTODO PRINCIPAL
    # ============================================================

    def analisar_posicoes(self, posicoes: List[Dict]) -> List[Dict]:

        decisoes = []

        logger.info(
            f"[AgenteVenda] Analisando {len(posicoes)} posições abertas"
        )

        for posicao in posicoes:

            try:

                decisao = self._analisar_posicao_individual(posicao)

                if decisao:
                    decisoes.append(decisao)

            except Exception as e:

                logger.error(
                    f"[AgenteVenda] Erro ao analisar posição "
                    f"{posicao.get('acao','DESCONHECIDO')} | {e}"
                )

        logger.info(
            f"[AgenteVenda] Decisões de venda geradas: {len(decisoes)}"
        )

        return decisoes

    # ============================================================
    # ANÁLISE INDIVIDUAL
    # ============================================================

    def _analisar_posicao_individual(self, posicao: Dict) -> Dict | None:

        acao = posicao.get("acao")
        preco_compra = posicao.get("preco_compra")
        preco_atual = posicao.get("preco_atual")
        quantidade = posicao.get("quantidade")

        if not acao or not preco_compra or not preco_atual or not quantidade:

            logger.warning(
                "[AgenteVenda] Dados inválidos para posição"
            )

            return None

        logger.info(f"[AgenteVenda] Reavaliando {acao}")

        # ========================================================
        # 1. CALCULAR SCORE ATUAL
        # ========================================================

        score_detalhado = calcular_score_completo(posicao)

        score_atual = score_detalhado["score_total"]

        # ========================================================
        # 2. CALCULAR RETORNO
        # ========================================================

        retorno = (preco_atual / preco_compra) - 1

        # ========================================================
        # 3. DEFINIR MOTIVO DE VENDA
        # ========================================================

        motivo = None

        # 🔴 STOP LOSS
        if retorno <= -0.15:
            motivo = "STOP_LOSS"

        # 🟡 Queda de qualidade do ativo
        elif score_atual < 60:
            motivo = "QUEDA_DE_SCORE"

        # 🟢 Realização de lucro
        elif retorno >= 0.25:
            motivo = "TAKE_PROFIT"

        # 🔵 risco externo
        elif not validar_venda(posicao):
            motivo = "RISCO_ELEVADO"

        if not motivo:

            logger.info(
                f"[AgenteVenda] {acao} mantido (sem sinal de venda)"
            )

            return None

        # ========================================================
        # 4. ESTRUTURA DA DECISÃO
        # ========================================================

        decisao = {
            "acao": acao,
            "quantidade": quantidade,
            "preco_venda": preco_atual,
            "preco_compra": preco_compra,
            "retorno_%": retorno * 100,
            "score_atual": score_atual,
            "motivo": motivo,
            "data": datetime.utcnow(),
            "status": "AGUARDANDO_APROVACAO"
        }

        logger.info(
            f"[AgenteVenda] {acao} sinal de VENDA | motivo={motivo}"
        )

        return decisao

    # ============================================================
    # EXECUÇÃO
    # ============================================================

    def executar_venda(self, decisao: Dict, aprovado: bool):

        if not aprovado:

            logger.info(
                f"[AgenteVenda] Venda recusada para {decisao['acao']}"
            )

            return

        try:

            registrar_ordem(
                acao=decisao["acao"],
                tipo="VENDA",
                quantidade=decisao["quantidade"],
                preco=decisao["preco_venda"],
                score=decisao["score_atual"]
            )

            logger.info(
                f"[AgenteVenda] Venda executada | {decisao['acao']}"
            )

        except Exception as e:

            logger.error(
                f"[AgenteVenda] Erro ao executar venda: {e}"
            )