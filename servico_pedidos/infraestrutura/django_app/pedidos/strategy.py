from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal


class FormaPagamento(ABC):

    @abstractmethod
    def processar(self, valor: Decimal) -> str:
        """Processa o pagamento e retorna mensagem de confirmação."""

    @abstractmethod
    def descricao(self) -> str:
        """Nome legível desta forma de pagamento."""


class PagamentoDinheiro(FormaPagamento):

    def processar(self, valor: Decimal) -> str:
        return f"Pagamento de R${valor:.2f} em dinheiro registrado."

    def descricao(self) -> str:
        return "Dinheiro"


class PagamentoCartao(FormaPagamento):

    def processar(self, valor: Decimal) -> str:
        return f"Pagamento de R${valor:.2f} no cartão processado."

    def descricao(self) -> str:
        return "Cartão"


class PagamentoPix(FormaPagamento):

    def processar(self, valor: Decimal) -> str:
        return f"Pagamento de R${valor:.2f} via Pix confirmado."

    def descricao(self) -> str:
        return "Pix"


# Nova forma de pagamento: criar classe acima e adicionar uma linha aqui.
_formas_de_pagamento: dict[str, type[FormaPagamento]] = {
    "dinheiro": PagamentoDinheiro,
    "cartao": PagamentoCartao,
    "pix": PagamentoPix,
}


def obter_forma_pagamento(nome: str) -> FormaPagamento:
    classe = _formas_de_pagamento.get(nome.lower())
    if classe is None:
        formas_validas = ", ".join(_formas_de_pagamento.keys())
        raise ValueError(f"Forma de pagamento '{nome}' inválida. Válidas: {formas_validas}.")
    return classe()
