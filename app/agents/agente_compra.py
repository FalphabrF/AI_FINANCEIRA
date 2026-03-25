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

# Este agente NÃO executa ordens.

# Ele apenas decide e envia para aprovação/execução.

# ============================================================

from typing import List, Dict
from datetime import datetime

from core.logger import logger
from models.scoring import calcular_score_completo
from models.risco import validar_compra
from models.portfolio import calcular_alocacao
from execution.executor import registrar_ordem
from core.config import SCORE_MINIMO_COMPRA

class AgenteCompra:
    """
    Classe principal do agente de compra.

    ```
    Esse agente é responsável por analisar ativos e decidir
    se devem ser comprados com base no modelo quantitativo.
    """

def __init__(self, capital_total: float, capital_disponivel: float):
    """
    Inicializa o agente com informações financeiras.

    :param capital_total: Capital total da conta
    :param capital_disponivel: Capital livre para investir
    """
    self.capital_total = capital_total
    self.capital_disponivel = capital_disponivel

    logger.info(f"[AgenteCompra] Inicializado com capital_total={capital_total} | capital_disponivel={capital_disponivel}")

# ============================================================
# MÉTODO PRINCIPAL
# ============================================================
def analisar_ativos(self, dados_ativos: List[Dict]) -> List[Dict]:
    """
    Analisa uma lista de ativos e retorna oportunidades de compra.

    :param dados_ativos: Lista de dicionários com dados dos ativos
    :return: Lista de oportunidades aprovadas
    """

    oportunidades = []

    logger.info(f"[AgenteCompra] Iniciando análise de {len(dados_ativos)} ativos")

    for ativo in dados_ativos:
        try:
            resultado = self._analisar_ativo_individual(ativo)

            if resultado:
                oportunidades.append(resultado)

        except Exception as e:
            logger.error(f"[AgenteCompra] Erro ao analisar ativo {ativo.get('acao')}: {e}")

    logger.info(f"[AgenteCompra] Total de oportunidades encontradas: {len(oportunidades)}")

    return oportunidades

# ============================================================
# ANÁLISE INDIVIDUAL
# ============================================================
def _analisar_ativo_individual(self, ativo: Dict) -> Dict:
    """
    Analisa um único ativo profundamente.

    :param ativo: Dados do ativo
    :return: Dicionário com decisão ou None
    """

    acao = ativo.get("acao")
    preco = ativo.get("preco")

    logger.info(f"[AgenteCompra] Analisando {acao}")

    # ========================================================
    # 1. CALCULAR SCORE COMPLETO
    # ========================================================
    score_detalhado = calcular_score_completo(ativo)

    score_final = score_detalhado["score_final"]

    logger.info(f"[AgenteCompra] {acao} | Score final: {score_final:.2f}")

    # ========================================================
    # 2. FILTRO DE SCORE
    # ========================================================
    if score_final < SCORE_MINIMO_COMPRA:
        logger.info(f"[AgenteCompra] {acao} descartado (score baixo)")
        return None

    # ========================================================
    # 3. VALIDAÇÃO DE RISCO
    # ========================================================
    risco_ok = validar_compra(ativo, self.capital_total)

    if not risco_ok:
        logger.warning(f"[AgenteCompra] {acao} reprovado por risco")
        return None

    # ========================================================
    # 4. CÁLCULO DE ALOCAÇÃO
    # ========================================================
    valor_alocado = calcular_alocacao(score_final, self.capital_total)

    if valor_alocado > self.capital_disponivel:
        logger.warning(f"[AgenteCompra] {acao} sem capital disponível suficiente")
        return None

    quantidade = int(valor_alocado // preco)

    if quantidade <= 0:
        logger.warning(f"[AgenteCompra] {acao} quantidade inválida para compra")
        return None

    # ========================================================
    # 5. ESTRUTURA DA DECISÃO
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

    logger.info(f"[AgenteCompra] {acao} APROVADO para compra | Qtd: {quantidade}")

    return decisao

# ============================================================
# EXECUÇÃO (APÓS APROVAÇÃO)
# ============================================================
def executar_compra(self, decisao: Dict, aprovado: bool):
    """
    Executa a compra após aprovação externa (ex: usuário).

    :param decisao: Dados da decisão
    :param aprovado: Boolean indicando aprovação
    """

    if not aprovado:
        logger.info(f"[AgenteCompra] Compra recusada para {decisao['acao']}")
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

        logger.info(f"[AgenteCompra] Compra executada com sucesso para {decisao['acao']}")

    except Exception as e:
        logger.error(f"[AgenteCompra] Erro ao executar compra: {e}")
