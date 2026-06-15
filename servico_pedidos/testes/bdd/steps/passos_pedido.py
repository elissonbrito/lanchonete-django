import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from decimal import Decimal
from unittest.mock import MagicMock
from behave import given, when, then, use_step_matcher

use_step_matcher("re")

from dominio.entidades.pedido import (
    FormaPagamento, ItemPedido, Pedido, StatusPedido, TipoPedido,
)
from dominio.servicos.servico_pedido import ServicoPedido


def _repositorio_mock(pedido_id=1):
    repo = MagicMock()
    repo.salvar.side_effect = lambda p: (setattr(p, "id", pedido_id) or p)
    return repo


@given('que o cliente "(?P<nome>.+)" quer fazer um pedido no balcão')
def passo_cliente_balcao(contexto, nome):
    contexto.nome_cliente = nome
    contexto.tipo = TipoPedido.BALCAO
    contexto.itens = []


@given('que o cliente "(?P<nome>.+)" quer fazer um pedido de entrega')
def passo_cliente_entrega(contexto, nome):
    contexto.nome_cliente = nome
    contexto.tipo = TipoPedido.ENTREGA
    contexto.itens = []


@given('o pedido contém o item "(?P<nome_produto>.+)" que custa R\$(?P<preco>\d+),00')
def passo_adicionar_item(contexto, nome_produto, preco):
    item = ItemPedido(produto_id=1, nome_produto=nome_produto, preco_unitario=Decimal(preco))
    contexto.itens.append(item)


@when('o cliente paga via "(?P<forma>.+)"')
def passo_pagar(contexto, forma):
    mapeamento = {
        "pix": FormaPagamento.PIX,
        "cartao": FormaPagamento.CARTAO,
        "dinheiro": FormaPagamento.DINHEIRO,
    }
    servico = ServicoPedido(_repositorio_mock())
    contexto.pedido, contexto.mensagem_pagamento = servico.criar_pedido(
        cliente=contexto.nome_cliente,
        tipo=contexto.tipo,
        forma_pagamento=mapeamento[forma.lower()],
        itens=contexto.itens,
    )


@then('o pedido deve ser criado com status "(?P<status>.+)"')
def passo_verificar_status(contexto, status):
    assert contexto.pedido.status.value == status


@then('o total do pedido deve ser R\$(?P<total>\d+),00')
def passo_verificar_total(contexto, total):
    assert contexto.pedido.calcular_total() == Decimal(total)


@then('a mensagem de pagamento deve mencionar "(?P<termo>.+)"')
def passo_verificar_mensagem(contexto, termo):
    assert termo.lower() in contexto.mensagem_pagamento.lower()


@given('que existe um pedido com status "(?P<status>.+)"')
def passo_pedido_com_status(contexto, status):
    contexto.pedido = Pedido(
        cliente="Teste", tipo=TipoPedido.BALCAO, forma_pagamento=FormaPagamento.PIX,
    )
    contexto.pedido.status = StatusPedido(status)


@when('o status do pedido avança')
def passo_avancar_status(contexto):
    contexto.pedido.avancar_status()


@then('o status do pedido deve ser "(?P<status>.+)"')
def passo_verificar_novo_status(contexto, status):
    assert contexto.pedido.status.value == status


@then('o pedido deve estar finalizado')
def passo_verificar_finalizado(contexto):
    assert contexto.pedido.esta_finalizado()
