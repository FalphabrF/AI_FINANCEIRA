# ============================================================
# AGENTE DE COMPRA
# ============================================================
# Responsável por:
# - Receber dados tratados do mercado
# - Aplicar modelo de scoring
# - Validar regras de risco
# - Verificar capital disponível
# - Gerar decisões de compra (NÃO executa diretamente)
#
# IMPORTANTE:
# Este agente NÃO executa ordens automaticamente.
# Ele apenas gera decisões estruturadas.
# ============================================================

from typing import List, Dict
from datetime import datetime

from app.core.logger import logger
from app.domain.scoring import calcular_score_completo
from app.domain.risco import validar_compra
from app.domain.portfolio import calcular_alocacao
from app.execution.executor import registrar_ordem
from app.core.config import SCORE_MINIMO_COMPRA


class AgenteCompra:
    """
    Agente responsável por identificar oportunidades de compra.
    """

    def __init__(self, capital_total: float, capital_disponivel: float):

        self.capital_total = capital_total
        self.capital_disponivel = capital_disponivel

        logger.info(
            f"[AgenteCompra] Inicializado | "
            f"capital_total={capital_total} | "
            f"capital_disponivel={capital_disponivel}"
        )

    # ============================================================
    # MÉTODO PRINCIPAL
    # ============================================================

    def analisar_ativos(self, dados_ativos: List[Dict]) -> List[Dict]:

        oportunidades = []

        logger.info(
            f"[AgenteCompra] Iniciando análise de {len(dados_ativos)} ativos"
        )

        for ativo in dados_ativos:

            try:

                resultado = self._analisar_ativo_individual(ativo)

                if resultado:
                    oportunidades.append(resultado)

            except Exception as e:

                logger.error(
                    f"[AgenteCompra] Erro ao analisar ativo "
                    f"{ativo.get('acao', 'DESCONHECIDO')} | {e}"
                )

        logger.info(
            f"[AgenteCompra] Oportunidades encontradas: {len(oportunidades)}"
        )

        return oportunidades

    # ============================================================
    # ANÁLISE INDIVIDUAL
    # ============================================================

    def _analisar_ativo_individual(self, ativo: Dict) -> Dict | None:

        acao = ativo.get("acao")
        preco = ativo.get("preco")

        if not acao or not preco:
            logger.warning("[AgenteCompra] Dados inválidos para ativo")
            return None

        logger.info(f"[AgenteCompra] Analisando {acao}")

        # ========================================================
        # 1. CALCULAR SCORE
        # ========================================================

        score_detalhado = calcular_score_completo(ativo)

        score_final = score_detalhado["score_total"]

        logger.info(
            f"[AgenteCompra] {acao} | Score final: {score_final:.2f}"
        )

        # ========================================================
        # 2. FILTRO DE SCORE
        # ========================================================

        if score_final < SCORE_MINIMO_COMPRA:

            logger.info(
                f"[AgenteCompra] {acao} descartado (score baixo)"
            )

            return None

        # ========================================================
        # 3. VALIDAÇÃO DE RISCO
        # ========================================================

        risco_ok = validar_compra(ativo, self.capital_total)

        if not risco_ok:

            logger.warning(
                f"[AgenteCompra] {acao} reprovado por risco"
            )

            return None

        # ========================================================
        # 4. CÁLCULO DE ALOCAÇÃO
        # ========================================================

        valor_alocado = calcular_alocacao(
            score_final,
            self.capital_total
        )

        if valor_alocado > self.capital_disponivel:

            logger.warning(
                f"[AgenteCompra] {acao} sem capital disponível"
            )

            return None

        quantidade = int(valor_alocado // preco)

        if quantidade <= 0:

            logger.warning(
                f"[AgenteCompra] {acao} quantidade inválida"
            )

            return None

        # ========================================================
        # 5. DECISÃO FINAL
        # ========================================================

        decisao = {
            "acao": acao,
            "preco": preco,
            "quantidade": quantidade,
            "score": score_final,
            "score_detalhado": score_detalhado,
            "valor_total": quantidade * preco,
            "data": datetime.utcnow(),
            "status": "AGUARDANDO_APROVACAO"
        }

        logger.info(
            f"[AgenteCompra] {acao} APROVADO | "
            f"Qtd={quantidade}"
        )

        return decisao

    # ============================================================
    # EXECUÇÃO (APÓS APROVAÇÃO)
    # ============================================================

    def executar_compra(self, decisao: Dict, aprovado: bool):

        if not aprovado:

            logger.info(
                f"[AgenteCompra] Compra recusada para {decisao['acao']}"
            )

            return

        try:

            registrar_ordem(
                acao=decisao["acao"],
                tipo="COMPRA",
                quantidade=decisao["quantidade"],
                preco=decisao["preco"],
                score=decisao["score"]
            )

            self.capital_disponivel -= decisao["valor_total"]

            logger.info(
                f"[AgenteCompra] Compra executada: {decisao['acao']}"
            )

        except Exception as e:

            logger.error(
                f"[AgenteCompra] Erro ao executar compra: {e}"
            )