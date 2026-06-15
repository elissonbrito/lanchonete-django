from __future__ import annotations
from decimal import Decimal
from ..entidades.pedido import FormaPagamento, ItemPedido, Pedido, TipoPedido
from ..repositorios.repositorio_pedido import RepositorioPedido

# ── Padrão Strategy — formas de pagamento ──────────────────────────────────

from abc import ABC, abstractmethod


class EstrategiaPagamento(ABC):

    @abstractmethod
    def processar(self, valor: Decimal) -> str:
        """Processa o pagamento e retorna mensagem de confirmação."""

    @abstractmethod
    def descricao(self) -> str:
        """Nome legível desta forma de pagamento."""


class PagamentoDinheiro(EstrategiaPagamento):

    def processar(self, valor: Decimal) -> str:
        return f"Pagamento de R${valor:.2f} em dinheiro registrado."

    def descricao(self) -> str:
        return "Dinheiro"


class PagamentoCartao(EstrategiaPagamento):

    def processar(self, valor: Decimal) -> str:
        return f"Pagamento de R${valor:.2f} no cartão processado."

    def descricao(self) -> str:
        return "Cartão"


class PagamentoPix(EstrategiaPagamento):

    def processar(self, valor: Decimal) -> str:
        return f"Pagamento de R${valor:.2f} via Pix confirmado."

    def descricao(self) -> str:
        return "Pix"


# Nova forma: criar classe acima e adicionar uma linha aqui.
_estrategias: dict[FormaPagamento, type[EstrategiaPagamento]] = {
    FormaPagamento.DINHEIRO: PagamentoDinheiro,
    FormaPagamento.CARTAO:   PagamentoCartao,
    FormaPagamento.PIX:      PagamentoPix,
}


def _obter_estrategia(forma: FormaPagamento) -> EstrategiaPagamento:
    classe = _estrategias.get(forma)
    if classe is None:
        raise ValueError(f"Forma de pagamento '{forma}' sem estratégia registrada.")
    return classe()


# ── Padrão Factory — tipos de pedido ──────────────────────────────────────

class PedidoBase(ABC):

    @abstractmethod
    def calcular_taxa_adicional(self) -> Decimal:
        """Taxa adicional específica deste tipo de pedido."""


class PedidoBalcao(PedidoBase):

    def calcular_taxa_adicional(self) -> Decimal:
        return Decimal("0.00")


class PedidoEntrega(PedidoBase):

    TAXA_ENTREGA = Decimal("5.00")

    def calcular_taxa_adicional(self) -> Decimal:
        return self.TAXA_ENTREGA


class PedidoMesa(PedidoBase):

    def calcular_taxa_adicional(self) -> Decimal:
        return Decimal("0.00")


# Nova entrada ao adicionar tipo.
_tipos_pedido: dict[TipoPedido, type[PedidoBase]] = {
    TipoPedido.BALCAO:  PedidoBalcao,
    TipoPedido.ENTREGA: PedidoEntrega,
    TipoPedido.MESA:    PedidoMesa,
}


class FabricaTipoPedido:

    @staticmethod
    def criar(tipo: TipoPedido) -> PedidoBase:
        classe = _tipos_pedido.get(tipo)
        if classe is None:
            raise ValueError(f"Tipo de pedido '{tipo}' não registrado na fábrica.")
        return classe()


# ── Padrão Observer — notificações de status ──────────────────────────────

class ObservadorPedido(ABC):

    @abstractmethod
    def atualizar(self, pedido_id: int, novo_status: str) -> None:
        """Reage à mudança de status de um pedido."""


class NotificadorCozinha(ObservadorPedido):

    def atualizar(self, pedido_id: int, novo_status: str) -> None:
        self.ultima_mensagem = f"[COZINHA] Pedido #{pedido_id} → {novo_status}"
        print(self.ultima_mensagem)


class NotificadorCliente(ObservadorPedido):

    def atualizar(self, pedido_id: int, novo_status: str) -> None:
        self.ultima_mensagem = f"[CLIENTE] Pedido #{pedido_id} está: {novo_status}"
        print(self.ultima_mensagem)


class GerenciadorNotificacoes:
    """Subject do Observer — notifica todos os observadores registrados."""

    def __init__(self) -> None:
        self._observadores: list[ObservadorPedido] = []

    def registrar(self, observador: ObservadorPedido) -> None:
        self._observadores.append(observador)

    def remover(self, observador: ObservadorPedido) -> None:
        self._observadores.remove(observador)

    def notificar(self, pedido_id: int, novo_status: str) -> None:
        for observador in self._observadores:
            observador.atualizar(pedido_id, novo_status)


def _criar_gerenciador_padrao() -> GerenciadorNotificacoes:
    gerenciador = GerenciadorNotificacoes()
    gerenciador.registrar(NotificadorCozinha())
    gerenciador.registrar(NotificadorCliente())
    return gerenciador


gerenciador_notificacoes = _criar_gerenciador_padrao()


# ── Padrão Singleton — configurações ──────────────────────────────────────

class ConfiguracaoLanchonete:
    """Configurações globais — existe uma única instância durante a execução."""

    _instancia: "ConfiguracaoLanchonete | None" = None

    def __new__(cls) -> "ConfiguracaoLanchonete":
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia.nome = "Lanchonete Django"
            cls._instancia.taxa_entrega = Decimal("5.00")
            cls._instancia.tempo_preparo_padrao_minutos = 20
        return cls._instancia

    def __repr__(self) -> str:
        return f"ConfiguracaoLanchonete(nome={self.nome!r})"


# ── Serviço de domínio ────────────────────────────────────────────────────

class ServicoPedido:
    """
    Orquestra os casos de uso do domínio de pedidos.

    Depende apenas de abstrações (RepositorioPedido) — nunca de Django ou banco.
    """

    def __init__(self, repositorio: RepositorioPedido) -> None:
        self._repositorio = repositorio

    def criar_pedido(
        self,
        cliente: str,
        tipo: TipoPedido,
        forma_pagamento: FormaPagamento,
        itens: list[ItemPedido],
        numero_mesa: int | None = None,
    ) -> tuple[Pedido, str]:
        pedido = Pedido(
            cliente=cliente,
            tipo=tipo,
            forma_pagamento=forma_pagamento,
            itens=itens,
            numero_mesa=numero_mesa,
        )

        estrategia = _obter_estrategia(forma_pagamento)
        mensagem_pagamento = estrategia.processar(pedido.calcular_total())

        pedido_salvo = self._repositorio.salvar(pedido)
        gerenciador_notificacoes.notificar(pedido_salvo.id, pedido_salvo.status.value)

        return pedido_salvo, mensagem_pagamento

    def atualizar_status(self, pedido_id: int, novo_status: str) -> Pedido:
        pedido = self._repositorio.buscar_por_id(pedido_id)
        if pedido is None:
            raise ValueError(f"Pedido #{pedido_id} não encontrado.")

        pedido.status = pedido.status.__class__(novo_status)
        pedido_atualizado = self._repositorio.salvar(pedido)
        gerenciador_notificacoes.notificar(pedido_id, novo_status)

        return pedido_atualizado

    def listar_pedidos(self, limite: int = 10) -> list[Pedido]:
        return self._repositorio.listar_recentes(limite)
