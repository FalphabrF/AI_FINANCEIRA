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

# Nenhum agente deve operar sem consultar este.

# ============================================================

from datetime import datetime
from typing import Dict, List

from core.logger import logger
from database.connection import get_connection

class AgenteFinanceiro:
    """
    Classe responsável por gerenciar toda a saúde financeira do sistema.
    """
def __init__(self):
    """
    Inicializa o agente financeiro carregando dados do banco.
    """
    self.capital_total = 0.0
    self.capital_investido = 0.0
    self.capital_disponivel = 0.0

    logger.info("[AgenteFinanceiro] Inicializando agente financeiro")

    self._carregar_estado_inicial()

# ============================================================
# CARREGAMENTO INICIAL
# ============================================================
def _carregar_estado_inicial(self):
    """
    Carrega dados financeiros do banco de dados.
    """

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Capital total mais recente
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

        # Capital investido (posição aberta)
        cursor.execute("""
            SELECT COALESCE(SUM(quantidade * preco), 0)
            FROM historico_operacoes
            WHERE tipo_operacao = 'COMPRA'
        """)
        investido = cursor.fetchone()[0]

        self.capital_investido = float(investido)

        self._atualizar_capital_disponivel()

        cursor.close()
        conn.close()

        logger.info(f"[AgenteFinanceiro] Estado carregado | Total: {self.capital_total} | Investido: {self.capital_investido}")

    except Exception as e:
        logger.error(f"[AgenteFinanceiro] Erro ao carregar estado: {e}")

# ============================================================
# ATUALIZAÇÕES
# ============================================================
def _atualizar_capital_disponivel(self):
    """
    Atualiza o capital disponível baseado no investido.
    """
    self.capital_disponivel = self.capital_total - self.capital_investido

# ============================================================
# CONSULTAS
# ============================================================
def obter_estado_financeiro(self) -> Dict:
    """
    Retorna o estado financeiro atual.

    :return: dicionário com dados financeiros
    """
    return {
        "capital_total": self.capital_total,
        "capital_investido": self.capital_investido,
        "capital_disponivel": self.capital_disponivel
    }

def pode_comprar(self, valor: float) -> bool:
    """
    Verifica se há capital disponível para compra.

    :param valor: valor necessário
    :return: True ou False
    """
    return valor <= self.capital_disponivel

# ============================================================
# OPERAÇÕES FINANCEIRAS
# ============================================================
def registrar_compra(self, valor: float):
    """
    Atualiza estado após uma compra.

    :param valor: valor da compra
    """
    self.capital_investido += valor
    self._atualizar_capital_disponivel()

    logger.info(f"[AgenteFinanceiro] Compra registrada | Valor: {valor}")

def registrar_venda(self, valor: float, lucro: float):
    """
    Atualiza estado após uma venda.

    :param valor: valor total da venda
    :param lucro: lucro obtido
    """
    self.capital_investido -= valor
    self.capital_total += lucro

    self._atualizar_capital_disponivel()

    logger.info(f"[AgenteFinanceiro] Venda registrada | Valor: {valor} | Lucro: {lucro}")

# ============================================================
# GESTÃO DE DÍVIDAS
# ============================================================
def adicionar_divida(self, descricao: str, valor: float, data_quitacao: datetime):
    """
    Adiciona uma nova dívida ao sistema.
    """

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO dividas (descricao, valor, data_quitacao)
            VALUES (%s, %s, %s)
        """, (descricao, valor, data_quitacao))

        conn.commit()
        cursor.close()
        conn.close()

        logger.info(f"[AgenteFinanceiro] Dívida adicionada: {descricao}")

    except Exception as e:
        logger.error(f"[AgenteFinanceiro] Erro ao adicionar dívida: {e}")

def limpar_dividas_quitadas(self):
    """
    Remove automaticamente dívidas quitadas.
    """

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

        logger.info("[AgenteFinanceiro] Dívidas quitadas removidas")

    except Exception as e:
        logger.error(f"[AgenteFinanceiro] Erro ao limpar dívidas: {e}")

# ============================================================
# HISTÓRICO FINANCEIRO
# ============================================================
def registrar_snapshot(self):
    """
    Salva o estado atual no banco (para análise histórica).
    """

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO capital (conservador, agressivo, data)
            VALUES (%s, %s, %s)
        """, (
            self.capital_disponivel,
            self.capital_investido,
            datetime.utcnow()
        ))

        conn.commit()
        cursor.close()
        conn.close()

        logger.info("[AgenteFinanceiro] Snapshot registrado")

    except Exception as e:
        logger.error(f"[AgenteFinanceiro] Erro ao registrar snapshot: {e}")
