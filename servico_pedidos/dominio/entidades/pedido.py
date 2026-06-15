from __future__ import annotations
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum


class StatusPedido(str, Enum):
    RECEBIDO   = "recebido"
    PREPARANDO = "preparando"
    PRONTO     = "pronto"
    ENTREGUE   = "entregue"


class TipoPedido(str, Enum):
    BALCAO  = "balcao"
    ENTREGA = "entrega"
    MESA    = "mesa"


class FormaPagamento(str, Enum):
    DINHEIRO = "dinheiro"
    CARTAO   = "cartao"
    PIX      = "pix"


@dataclass
class ItemPedido:
    produto_id: int
    nome_produto: str
    preco_unitario: Decimal
    quantidade: int = 1

    @property
    def subtotal(self) -> Decimal:
        return self.preco_unitario * self.quantidade


@dataclass
class Pedido:
    """Entidade central do domínio — não depende de nenhum framework."""

    cliente: str
    tipo: TipoPedido
    forma_pagamento: FormaPagamento
    itens: list[ItemPedido] = field(default_factory=list)
    status: StatusPedido = StatusPedido.RECEBIDO
    numero_mesa: int | None = None
    id: int | None = None

    TAXA_ENTREGA = Decimal("5.00")

    def calcular_total(self) -> Decimal:
        subtotal = sum(item.subtotal for item in self.itens)
        if self.tipo == TipoPedido.ENTREGA:
            return subtotal + self.TAXA_ENTREGA
        return subtotal

    def avancar_status(self) -> None:
        """Avança o status seguindo o fluxo natural do pedido."""
        fluxo = [
            StatusPedido.RECEBIDO,
            StatusPedido.PREPARANDO,
            StatusPedido.PRONTO,
            StatusPedido.ENTREGUE,
        ]
        indice_atual = fluxo.index(self.status)
        if indice_atual < len(fluxo) - 1:
            self.status = fluxo[indice_atual + 1]

    def esta_finalizado(self) -> bool:
        return self.status == StatusPedido.ENTREGUE
