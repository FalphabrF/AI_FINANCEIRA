# ============================================================

# N8N HOOKS - INTEGRAÇÃO COM AUTOMAÇÃO

# ============================================================

# Responsável por:

# - Enviar eventos para o n8n (webhooks)

# - Receber respostas (aprovação/rejeição)

# - Padronizar comunicação entre sistema e automações

#

# FLUXOS:

# - Solicitação de compra

# - Solicitação de venda

# - Alertas gerais

#

# IMPORTANTE:

# Este módulo NÃO toma decisão.

# Ele apenas comunica eventos externos.

# ============================================================

import requests
from typing import Dict, Optional
from datetime import datetime

from core.logger import logger
from core.config import N8N_WEBHOOK_URL

# ============================================================

# CLASSE PRINCIPAL

# ============================================================

class N8NHooks:
    """
    Classe responsável pela comunicação com o n8n.
    """

def __init__(self, webhook_url: Optional[str] = None):
    """
    Inicializa o cliente de integração.

    :param webhook_url: URL do webhook do n8n
    """
    self.webhook_url = webhook_url or N8N_WEBHOOK_URL

    logger.info(f"[N8NHooks] Inicializado com webhook: {self.webhook_url}")

# ============================================================
# MÉTODO BASE DE ENVIO
# ============================================================
def _enviar_webhook(self, payload: Dict) -> Dict:
    """
    Envia dados para o n8n via POST.

    :param payload: Dados estruturados
    :return: Resposta do webhook
    """

    try:
        response = requests.post(
            self.webhook_url,
            json=payload,
            timeout=10
        )

        response.raise_for_status()

        logger.info(f"[N8NHooks] Webhook enviado com sucesso | Tipo: {payload.get('tipo')}")

        return response.json() if response.content else {}

    except requests.exceptions.RequestException as e:
        logger.error(f"[N8NHooks] Erro ao enviar webhook: {e}")
        return {"erro": str(e)}

# ============================================================
# SOLICITAÇÃO DE COMPRA
# ============================================================
def solicitar_aprovacao_compra(self, decisao: Dict) -> Dict:
    """
    Envia solicitação de aprovação de compra.

    :param decisao: Dados da decisão do agente de compra
    """

    payload = {
        "tipo": "COMPRA",
        "acao": decisao["acao"],
        "quantidade": decisao["quantidade"],
        "preco": decisao["preco"],
        "valor_total": decisao["valor_total"],
        "score": decisao["score"],
        "data": str(datetime.utcnow()),
        "status": "AGUARDANDO_APROVACAO",
        "metadata": {
            "score_detalhado": decisao.get("score_detalhado", {})
        }
    }

    logger.info(f"[N8NHooks] Solicitando aprovação de COMPRA para {decisao['acao']}")

    return self._enviar_webhook(payload)

# ============================================================
# SOLICITAÇÃO DE VENDA
# ============================================================
def solicitar_aprovacao_venda(self, decisao: Dict) -> Dict:
    """
    Envia solicitação de aprovação de venda.

    :param decisao: Dados da decisão do agente de venda
    """

    payload = {
        "tipo": "VENDA",
        "acao": decisao["acao"],
        "quantidade": decisao["quantidade"],
        "preco": decisao["preco_venda"],
        "preco_compra": decisao["preco_compra"],
        "retorno_%": decisao["retorno_%"],
        "score_atual": decisao["score_atual"],
        "motivo": decisao["motivo"],
        "data": str(datetime.utcnow()),
        "status": "AGUARDANDO_APROVACAO"
    }

    logger.info(f"[N8NHooks] Solicitando aprovação de VENDA para {decisao['acao']}")

    return self._enviar_webhook(payload)

# ============================================================
# ALERTAS GERAIS
# ============================================================
def enviar_alerta(self, mensagem: str, nivel: str = "INFO") -> Dict:
    """
    Envia alertas genéricos para o n8n.

    :param mensagem: Texto do alerta
    :param nivel: INFO | WARNING | ERROR
    """

    payload = {
        "tipo": "ALERTA",
        "nivel": nivel,
        "mensagem": mensagem,
        "data": str(datetime.utcnow())
    }

    logger.info(f"[N8NHooks] Enviando alerta: {mensagem}")

    return self._enviar_webhook(payload)

# ============================================================
# PROCESSAMENTO DE RESPOSTA
# ============================================================
def interpretar_resposta(self, resposta: Dict) -> bool:
    """
    Interpreta resposta do n8n (aprovação).

    :param resposta: JSON retornado
    :return: True (aprovado) ou False
    """

    if not resposta:
        logger.warning("[N8NHooks] Resposta vazia - assumindo NÃO aprovado")
        return False

    aprovado = resposta.get("aprovado")

    if aprovado is True:
        logger.info("[N8NHooks] Operação APROVADA")
        return True

    logger.info("[N8NHooks] Operação REJEITADA")
    return False

