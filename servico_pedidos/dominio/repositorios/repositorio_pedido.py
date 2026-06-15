from __future__ import annotations
from abc import ABC, abstractmethod
from ..entidades.pedido import Pedido


class RepositorioPedido(ABC):
    """Porta de saída — o domínio depende desta abstração, nunca do banco."""

    @abstractmethod
    def salvar(self, pedido: Pedido) -> Pedido:
        """Persiste o pedido e retorna com o id preenchido."""

    @abstractmethod
    def buscar_por_id(self, pedido_id: int) -> Pedido | None:
        """Retorna o pedido ou None se não existir."""

    @abstractmethod
    def listar_recentes(self, limite: int = 10) -> list[Pedido]:
        """Retorna os pedidos mais recentes."""
