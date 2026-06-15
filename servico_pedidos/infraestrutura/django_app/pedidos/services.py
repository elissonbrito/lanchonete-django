from __future__ import annotations

from decimal import Decimal

from .factory import FabricaPedido
from .models import ItemPedido, Pedido, Produto, StatusPedido, TipoPedido
from .observer import gerenciador_status
from .strategy import obter_forma_pagamento


def _calcular_preco_itens(ids_produtos: list[str]) -> Decimal:
    return sum(Produto.objects.get(pk=pid).preco for pid in ids_produtos)


def _salvar_pedido(
    *,
    cliente: str,
    tipo: str,
    forma_pagamento: str,
    numero_mesa: int | None,
    total: Decimal,
) -> Pedido:
    return Pedido.objects.create(
        cliente=cliente,
        tipo=tipo,
        forma_pagamento=forma_pagamento,
        numero_mesa=numero_mesa,
        total=total,
        status=StatusPedido.RECEBIDO,
    )


def _salvar_itens_do_pedido(pedido: Pedido, ids_produtos: list[str]) -> None:
    for pid in ids_produtos:
        produto = Produto.objects.get(pk=pid)
        ItemPedido.objects.create(pedido=pedido, produto=produto, quantidade=1)


def processar_novo_pedido(
    *,
    cliente: str,
    tipo: str,
    forma_pagamento: str,
    numero_mesa: int | None,
    ids_produtos: list[str],
) -> tuple[Pedido, str]:
    """Orquestra criação, cálculo, persistência e notificação de um novo pedido."""
    kwargs: dict = {}
    if tipo == TipoPedido.MESA and numero_mesa:
        kwargs["numero_mesa"] = int(numero_mesa)

    pedido_dominio = FabricaPedido.criar(tipo=tipo, itens=ids_produtos, cliente=cliente, **kwargs)

    preco_itens = _calcular_preco_itens(ids_produtos)
    total = pedido_dominio.calcular_total(preco_itens)

    estrategia = obter_forma_pagamento(forma_pagamento)
    mensagem_pagamento = estrategia.processar(total)

    pedido_salvo = _salvar_pedido(
        cliente=cliente,
        tipo=tipo,
        forma_pagamento=forma_pagamento,
        numero_mesa=numero_mesa,
        total=total,
    )
    _salvar_itens_do_pedido(pedido_salvo, ids_produtos)
    gerenciador_status.notificar(pedido_salvo.pk, StatusPedido.RECEBIDO)

    return pedido_salvo, mensagem_pagamento


def atualizar_status_pedido(pedido: Pedido, novo_status: str) -> None:
    """Persiste o novo status e notifica todos os observadores."""
    pedido.status = novo_status
    pedido.save(update_fields=["status"])
    gerenciador_status.notificar(pedido.pk, novo_status)
