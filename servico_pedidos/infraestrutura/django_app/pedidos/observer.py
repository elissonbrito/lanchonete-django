from __future__ import annotations

from abc import ABC, abstractmethod


class Observador(ABC):

    @abstractmethod
    def atualizar(self, pedido_id: int, novo_status: str) -> None:
        """Reage à mudança de status de um pedido."""


class NotificadorCozinha(Observador):

    def atualizar(self, pedido_id: int, novo_status: str) -> None:
        self.ultima_mensagem = f"[COZINHA] Pedido #{pedido_id} → {novo_status}"
        print(self.ultima_mensagem)


class NotificadorCliente(Observador):

    def atualizar(self, pedido_id: int, novo_status: str) -> None:
        self.ultima_mensagem = f"[CLIENTE] Seu pedido #{pedido_id} está: {novo_status}"
        print(self.ultima_mensagem)


class GerenciadorStatus:
    """Notifica todos os observadores registrados quando o status de um pedido muda."""

    def __init__(self) -> None:
        self._observadores: list[Observador] = []

    def registrar(self, observador: Observador) -> None:
        self._observadores.append(observador)

    def remover(self, observador: Observador) -> None:
        self._observadores.remove(observador)

    def notificar(self, pedido_id: int, novo_status: str) -> None:
        for observador in self._observadores:
            observador.atualizar(pedido_id, novo_status)


def _criar_gerenciador_padrao() -> GerenciadorStatus:
    gerenciador = GerenciadorStatus()
    gerenciador.registrar(NotificadorCozinha())
    gerenciador.registrar(NotificadorCliente())
    return gerenciador


gerenciador_status = _criar_gerenciador_padrao()
