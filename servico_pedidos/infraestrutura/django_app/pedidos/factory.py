from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal


class PedidoBase(ABC):

    def __init__(self, itens: list[str], cliente: str) -> None:
        self.itens = itens
        self.cliente = cliente

    @abstractmethod
    def descricao(self) -> str:
        """Descrição legível do tipo de pedido."""

    @abstractmethod
    def calcular_total(self, preco_itens: Decimal) -> Decimal:
        """Calcula o valor total considerando eventuais taxas."""


class PedidoBalcao(PedidoBase):

    def descricao(self) -> str:
        return "Retirada no balcão"

    def calcular_total(self, preco_itens: Decimal) -> Decimal:
        return preco_itens


class PedidoEntrega(PedidoBase):

    TAXA_ENTREGA = Decimal("5.00")

    def descricao(self) -> str:
        return "Entrega em domicílio"

    def calcular_total(self, preco_itens: Decimal) -> Decimal:
        return preco_itens + self.TAXA_ENTREGA


class PedidoMesa(PedidoBase):

    def __init__(self, itens: list[str], cliente: str, numero_mesa: int = 1) -> None:
        super().__init__(itens, cliente)
        self.numero_mesa = numero_mesa

    def descricao(self) -> str:
        return f"Mesa {self.numero_mesa}"

    def calcular_total(self, preco_itens: Decimal) -> Decimal:
        return preco_itens


# Novo tipo de pedido: criar classe acima e adicionar uma linha aqui.
_tipos_de_pedido: dict[str, type[PedidoBase]] = {
    "balcao": PedidoBalcao,
    "entrega": PedidoEntrega,
    "mesa": PedidoMesa,
}


class FabricaPedido:
    """Centraliza a criação de pedidos, isolando o código cliente das classes concretas."""

    @staticmethod
    def criar(tipo: str, itens: list[str], cliente: str, **kwargs) -> PedidoBase:
        classe = _tipos_de_pedido.get(tipo.lower())
        if classe is None:
            tipos_validos = ", ".join(_tipos_de_pedido.keys())
            raise ValueError(f"Tipo de pedido '{tipo}' inválido. Válidos: {tipos_validos}.")
        return classe(itens=itens, cliente=cliente, **kwargs)
