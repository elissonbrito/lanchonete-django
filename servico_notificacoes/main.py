"""
Microsserviço de Notificações — responsabilidade única:
receber eventos de status e registrá-los.

Em produção, este serviço enviaria e-mails, SMS ou push notifications.
Aqui, registra em log para fins didáticos.
"""
from flask import Flask, jsonify, request
import logging

aplicacao = Flask(__name__)
logging.basicConfig(level=logging.INFO)
_log = logging.getLogger(__name__)

_historico_notificacoes: list[dict] = []


@aplicacao.route("/notificar", methods=["POST"])
def notificar():
    dados = request.get_json()
    pedido_id = dados.get("pedido_id")
    novo_status = dados.get("status")

    notificacao = {"pedido_id": pedido_id, "status": novo_status}
    _historico_notificacoes.append(notificacao)
    _log.info("[NOTIFICAÇÃO] Pedido #%s → %s", pedido_id, novo_status)

    return jsonify({"mensagem": "Notificação registrada.", "dados": notificacao}), 201


@aplicacao.route("/historico", methods=["GET"])
def historico():
    return jsonify(_historico_notificacoes)


@aplicacao.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    aplicacao.run(host="0.0.0.0", port=8003)
