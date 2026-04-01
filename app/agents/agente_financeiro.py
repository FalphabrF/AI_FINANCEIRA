# ============================================================
# AGENTE FINANCEIRO
# ============================================================
# Responsável por:
# - Gerenciar capital total e disponível
# - Controlar entradas e saídas
# - Gerenciar dívidas
# - Atualizar estado financeiro do sistema
# - Servir como base para decisões dos agentes
#
# IMPORTANTE:
# Este agente é a FONTE DA VERDADE financeira do sistema.
# ============================================================

from datetime import datetime
from typing import Dict

from app.core.logger import logger
from app.infrastructure.database.connection import get_connection


class AgenteFinanceiro:
    """
    Gerencia toda a saúde financeira do sistema.
    """

    def __init__(self):

        self.capital_total = 0.0
        self.capital_investido = 0.0
        self.capital_disponivel = 0.0

        logger.info("[AgenteFinanceiro] Inicializando")

        self._carregar_estado_inicial()

    # ============================================================
    # CARREGAMENTO INICIAL
    # ============================================================

    def _carregar_estado_inicial(self):

        try:

            conn = get_connection()
            cursor = conn.cursor()

            # ----------------------------------------------------
            # CAPITAL TOTAL
            # ----------------------------------------------------

            cursor.execute("""
                SELECT conservador + agressivo
                FROM capital
                ORDER BY data DESC
                LIMIT 1
            """)

            resultado = cursor.fetchone()

            if resultado:
                self.capital_total = float(resultado[0])
            else:
                self.capital_total = 0.0

            # ----------------------------------------------------
            # CAPITAL INVESTIDO
            # ----------------------------------------------------

            cursor.execute("""
                SELECT
                    COALESCE(
                        SUM(
                            CASE
                                WHEN tipo_operacao = 'COMPRA'
                                THEN quantidade * preco
                                WHEN tipo_operacao = 'VENDA'
                                THEN -(quantidade * preco)
                            END
                        ), 0
                    )
                FROM historico_operacoes
            """)

            investido = cursor.fetchone()[0]

            self.capital_investido = float(investido)

            self._atualizar_capital_disponivel()

            cursor.close()
            conn.close()

            logger.info(
                f"[AgenteFinanceiro] Estado carregado | "
                f"Total={self.capital_total} | "
                f"Investido={self.capital_investido} | "
                f"Disponível={self.capital_disponivel}"
            )

        except Exception as e:

            logger.error(
                f"[AgenteFinanceiro] Erro ao carregar estado: {e}"
            )

    # ============================================================
    # ATUALIZAÇÕES INTERNAS
    # ============================================================

    def _atualizar_capital_disponivel(self):

        self.capital_disponivel = self.capital_total - self.capital_investido

    # ============================================================
    # CONSULTAS
    # ============================================================

    def obter_estado_financeiro(self) -> Dict:

        return {
            "capital_total": self.capital_total,
            "capital_investido": self.capital_investido,
            "capital_disponivel": self.capital_disponivel
        }

    def pode_comprar(self, valor: float) -> bool:

        if valor <= 0:
            return False

        return valor <= self.capital_disponivel

    # ============================================================
    # REGISTROS FINANCEIROS
    # ============================================================

    def registrar_compra(self, valor: float):

        if valor <= 0:
            return

        self.capital_investido += valor

        self._atualizar_capital_disponivel()

        logger.info(
            f"[AgenteFinanceiro] Compra registrada | valor={valor}"
        )

    def registrar_venda(self, valor: float, lucro: float):

        if valor <= 0:
            return

        self.capital_investido -= valor

        self.capital_total += lucro

        self._atualizar_capital_disponivel()

        logger.info(
            f"[AgenteFinanceiro] Venda registrada | "
            f"valor={valor} | lucro={lucro}"
        )

    # ============================================================
    # GESTÃO DE DÍVIDAS
    # ============================================================

    def adicionar_divida(
        self,
        descricao: str,
        valor: float,
        data_quitacao: datetime
    ):

        try:

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO dividas
                (descricao, valor, data_quitacao)
                VALUES (%s, %s, %s)
            """, (descricao, valor, data_quitacao))

            conn.commit()

            cursor.close()
            conn.close()

            logger.info(
                f"[AgenteFinanceiro] Dívida adicionada | {descricao}"
            )

        except Exception as e:

            logger.error(
                f"[AgenteFinanceiro] Erro ao adicionar dívida: {e}"
            )

    def limpar_dividas_quitadas(self):

        try:

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM dividas
                WHERE data_quitacao <= NOW()
            """)

            conn.commit()

            cursor.close()
            conn.close()

            logger.info(
                "[AgenteFinanceiro] Dívidas quitadas removidas"
            )

        except Exception as e:

            logger.error(
                f"[AgenteFinanceiro] Erro ao limpar dívidas: {e}"
            )

    # ============================================================
    # SNAPSHOT HISTÓRICO
    # ============================================================

    def registrar_snapshot(self):

        try:

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO capital
                (conservador, agressivo, data)
                VALUES (%s, %s, %s)
            """, (
                self.capital_disponivel,
                self.capital_investido,
                datetime.utcnow()
            ))

            conn.commit()

            cursor.close()
            conn.close()

            logger.info(
                "[AgenteFinanceiro] Snapshot registrado"
            )

        except Exception as e:

            logger.error(
                f"[AgenteFinanceiro] Erro ao registrar snapshot: {e}"
            )