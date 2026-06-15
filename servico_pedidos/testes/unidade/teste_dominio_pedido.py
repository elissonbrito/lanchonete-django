"""
Testes de unidade do domínio de pedidos — escritos com TDD.

Cada teste:
  1. Define o comportamento esperado (Red)
  2. O código foi escrito para fazê-lo passar (Green)
  3. O código foi refatorado mantendo o teste verde (Refactor)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

import unittest
from decimal import Decimal
from unittest.mock import MagicMock

from dominio.entidades.pedido import (
    FormaPagamento,
    ItemPedido,
    Pedido,
    StatusPedido,
    TipoPedido,
)
from dominio.servicos.servico_pedido import (
    ConfiguracaoLanchonete,
    FabricaTipoPedido,
    GerenciadorNotificacoes,
    ObservadorPedido,
    PagamentoCartao,
    PagamentoDinheiro,
    PagamentoPix,
    PedidoBalcao,
    PedidoEntrega,
    PedidoMesa,
    ServicoPedido,
)


# ── Entidade Pedido ───────────────────────────────────────────────────────

class TestesEntidadePedido(unittest.TestCase):

    def _criar_item(self, preco: str = "20.00", quantidade: int = 1) -> ItemPedido:
        return ItemPedido(
            produto_id=1,
            nome_produto="X-Burguer",
            preco_unitario=Decimal(preco),
            quantidade=quantidade,
        )

    def test_subtotal_do_item_multiplica_preco_por_quantidade(self):
        item = self._criar_item(preco="10.00", quantidade=3)
        self.assertEqual(item.subtotal, Decimal("30.00"))

    def test_pedido_balcao_sem_taxa(self):
        pedido = Pedido(
            cliente="Ana",
            tipo=TipoPedido.BALCAO,
            forma_pagamento=FormaPagamento.PIX,
            itens=[self._criar_item("30.00")],
        )
        self.assertEqual(pedido.calcular_total(), Decimal("30.00"))

    def test_pedido_entrega_adiciona_taxa(self):
        pedido = Pedido(
            cliente="Bruno",
            tipo=TipoPedido.ENTREGA,
            forma_pagamento=FormaPagamento.CARTAO,
            itens=[self._criar_item("30.00")],
        )
        self.assertEqual(pedido.calcular_total(), Decimal("35.00"))

    def test_status_inicial_e_recebido(self):
        pedido = Pedido(cliente="Carla", tipo=TipoPedido.MESA, forma_pagamento=FormaPagamento.DINHEIRO)
        self.assertEqual(pedido.status, StatusPedido.RECEBIDO)

    def test_avancar_status_segue_fluxo(self):
        pedido = Pedido(cliente="Diego", tipo=TipoPedido.BALCAO, forma_pagamento=FormaPagamento.PIX)
        pedido.avancar_status()
        self.assertEqual(pedido.status, StatusPedido.PREPARANDO)
        pedido.avancar_status()
        self.assertEqual(pedido.status, StatusPedido.PRONTO)

    def test_pedido_entregue_esta_finalizado(self):
        pedido = Pedido(cliente="Eva", tipo=TipoPedido.BALCAO, forma_pagamento=FormaPagamento.PIX)
        pedido.status = StatusPedido.ENTREGUE
        self.assertTrue(pedido.esta_finalizado())

    def test_pedido_nao_finalizado_retorna_falso(self):
        pedido = Pedido(cliente="Fábio", tipo=TipoPedido.BALCAO, forma_pagamento=FormaPagamento.PIX)
        self.assertFalse(pedido.esta_finalizado())


# ── Strategy — Pagamento ──────────────────────────────────────────────────

class TestesEstrategiaPagamento(unittest.TestCase):

    _valor = Decimal("50.00")

    def test_dinheiro_menciona_dinheiro_na_mensagem(self):
        mensagem = PagamentoDinheiro().processar(self._valor)
        self.assertIn("dinheiro", mensagem.lower())

    def test_cartao_menciona_cartao_na_mensagem(self):
        mensagem = PagamentoCartao().processar(self._valor)
        self.assertIn("cartão", mensagem.lower())

    def test_pix_menciona_pix_na_mensagem(self):
        mensagem = PagamentoPix().processar(self._valor)
        self.assertIn("pix", mensagem.lower())

    def test_todas_as_mensagens_contem_o_valor(self):
        for estrategia in [PagamentoDinheiro(), PagamentoCartao(), PagamentoPix()]:
            with self.subTest(estrategia=estrategia.descricao()):
                self.assertIn("50.00", estrategia.processar(self._valor))


# ── Factory — Tipo de Pedido ──────────────────────────────────────────────

class TestesFabricaTipoPedido(unittest.TestCase):

    def test_cria_balcao(self):
        self.assertIsInstance(FabricaTipoPedido.criar(TipoPedido.BALCAO), PedidoBalcao)

    def test_cria_entrega(self):
        self.assertIsInstance(FabricaTipoPedido.criar(TipoPedido.ENTREGA), PedidoEntrega)

    def test_cria_mesa(self):
        self.assertIsInstance(FabricaTipoPedido.criar(TipoPedido.MESA), PedidoMesa)

    def test_entrega_tem_taxa(self):
        tipo = FabricaTipoPedido.criar(TipoPedido.ENTREGA)
        self.assertEqual(tipo.calcular_taxa_adicional(), Decimal("5.00"))

    def test_balcao_sem_taxa(self):
        tipo = FabricaTipoPedido.criar(TipoPedido.BALCAO)
        self.assertEqual(tipo.calcular_taxa_adicional(), Decimal("0.00"))


# ── Observer — Notificações ───────────────────────────────────────────────

class _ObservadorEspia(ObservadorPedido):
    def __init__(self):
        self.chamadas: list[tuple[int, str]] = []

    def atualizar(self, pedido_id: int, novo_status: str) -> None:
        self.chamadas.append((pedido_id, novo_status))


class TestesGerenciadorNotificacoes(unittest.TestCase):

    def test_observador_registrado_recebe_notificacao(self):
        gerenciador = GerenciadorNotificacoes()
        espia = _ObservadorEspia()
        gerenciador.registrar(espia)
        gerenciador.notificar(1, "pronto")
        self.assertEqual(espia.chamadas, [(1, "pronto")])

    def test_observador_removido_nao_recebe_notificacao(self):
        gerenciador = GerenciadorNotificacoes()
        espia = _ObservadorEspia()
        gerenciador.registrar(espia)
        gerenciador.remover(espia)
        gerenciador.notificar(1, "pronto")
        self.assertEqual(espia.chamadas, [])

    def test_multiplos_observadores_sao_notificados(self):
        gerenciador = GerenciadorNotificacoes()
        espia_1, espia_2 = _ObservadorEspia(), _ObservadorEspia()
        gerenciador.registrar(espia_1)
        gerenciador.registrar(espia_2)
        gerenciador.notificar(7, "preparando")
        self.assertEqual(len(espia_1.chamadas), 1)
        self.assertEqual(len(espia_2.chamadas), 1)


# ── Singleton — Configuração ──────────────────────────────────────────────

class TestesConfiguracaoLanchonete(unittest.TestCase):

    def test_retorna_sempre_a_mesma_instancia(self):
        self.assertIs(ConfiguracaoLanchonete(), ConfiguracaoLanchonete())

    def test_nome_padrao(self):
        self.assertEqual(ConfiguracaoLanchonete().nome, "Lanchonete Django")

    def test_taxa_entrega_padrao(self):
        self.assertEqual(ConfiguracaoLanchonete().taxa_entrega, Decimal("5.00"))


# ── Serviço de Domínio ────────────────────────────────────────────────────

class TestesServicoPedido(unittest.TestCase):

    def _repositorio_mock(self) -> MagicMock:
        """Repositório falso — isola o domínio do banco de dados."""
        repo = MagicMock()
        repo.salvar.side_effect = lambda p: (setattr(p, "id", 99) or p)
        return repo

    def test_criar_pedido_retorna_pedido_com_id(self):
        servico = ServicoPedido(self._repositorio_mock())
        item = ItemPedido(produto_id=1, nome_produto="Suco", preco_unitario=Decimal("8.00"))
        pedido, _ = servico.criar_pedido(
            cliente="Gabi",
            tipo=TipoPedido.BALCAO,
            forma_pagamento=FormaPagamento.PIX,
            itens=[item],
        )
        self.assertEqual(pedido.id, 99)

    def test_criar_pedido_retorna_mensagem_de_pagamento(self):
        servico = ServicoPedido(self._repositorio_mock())
        item = ItemPedido(produto_id=1, nome_produto="Suco", preco_unitario=Decimal("8.00"))
        _, mensagem = servico.criar_pedido(
            cliente="Hélio",
            tipo=TipoPedido.BALCAO,
            forma_pagamento=FormaPagamento.PIX,
            itens=[item],
        )
        self.assertIn("pix", mensagem.lower())

    def test_atualizar_status_levanta_excecao_para_pedido_inexistente(self):
        repo = MagicMock()
        repo.buscar_por_id.return_value = None
        servico = ServicoPedido(repo)
        with self.assertRaises(ValueError):
            servico.atualizar_status(999, "pronto")


if __name__ == "__main__":
    unittest.main()
