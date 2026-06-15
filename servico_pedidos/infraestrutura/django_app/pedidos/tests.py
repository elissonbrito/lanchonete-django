from decimal import Decimal

from django.test import TestCase

from .factory import FabricaPedido, PedidoBalcao, PedidoEntrega, PedidoMesa
from .observer import GerenciadorStatus, Observador
from .singleton import ConfiguracaoLanchonete
from .strategy import (
    PagamentoCartao,
    PagamentoDinheiro,
    PagamentoPix,
    obter_forma_pagamento,
)


class TestesConfiguracaoLanchonete(TestCase):

    def test_retorna_sempre_a_mesma_instancia(self):
        instancia_a = ConfiguracaoLanchonete()
        instancia_b = ConfiguracaoLanchonete()
        self.assertIs(instancia_a, instancia_b)

    def test_nome_padrao_correto(self):
        configuracao = ConfiguracaoLanchonete()
        self.assertEqual(configuracao.nome, "Lanchonete Django")

    def test_taxa_entrega_padrao_correta(self):
        configuracao = ConfiguracaoLanchonete()
        self.assertEqual(configuracao.taxa_entrega, 5.00)


class TestesFabricaPedido(TestCase):

    _itens = ["1", "2"]
    _cliente = "Maria"

    def test_cria_pedido_balcao(self):
        pedido = FabricaPedido.criar("balcao", self._itens, self._cliente)
        self.assertIsInstance(pedido, PedidoBalcao)

    def test_cria_pedido_entrega(self):
        pedido = FabricaPedido.criar("entrega", self._itens, self._cliente)
        self.assertIsInstance(pedido, PedidoEntrega)

    def test_cria_pedido_mesa_com_numero(self):
        pedido = FabricaPedido.criar("mesa", self._itens, self._cliente, numero_mesa=3)
        self.assertIsInstance(pedido, PedidoMesa)
        self.assertEqual(pedido.numero_mesa, 3)

    def test_tipo_invalido_levanta_excecao(self):
        with self.assertRaises(ValueError):
            FabricaPedido.criar("invalido", self._itens, self._cliente)


class TestesCalculoTotalPedido(TestCase):

    def test_balcao_sem_taxa(self):
        pedido = PedidoBalcao(itens=[], cliente="João")
        self.assertEqual(pedido.calcular_total(Decimal("30.00")), Decimal("30.00"))

    def test_entrega_adiciona_taxa(self):
        pedido = PedidoEntrega(itens=[], cliente="João")
        self.assertEqual(pedido.calcular_total(Decimal("30.00")), Decimal("35.00"))

    def test_mesa_sem_taxa(self):
        pedido = PedidoMesa(itens=[], cliente="João", numero_mesa=2)
        self.assertEqual(pedido.calcular_total(Decimal("30.00")), Decimal("30.00"))


class TestesFormaPagamento(TestCase):

    _valor = Decimal("50.00")

    def test_dinheiro_retorna_mensagem_correta(self):
        mensagem = PagamentoDinheiro().processar(self._valor)
        self.assertIn("dinheiro", mensagem.lower())
        self.assertIn("50.00", mensagem)

    def test_cartao_retorna_mensagem_correta(self):
        mensagem = PagamentoCartao().processar(self._valor)
        self.assertIn("cartão", mensagem.lower())

    def test_pix_retorna_mensagem_correta(self):
        mensagem = PagamentoPix().processar(self._valor)
        self.assertIn("pix", mensagem.lower())

    def test_obter_forma_pagamento_retorna_instancia_correta(self):
        estrategia = obter_forma_pagamento("pix")
        self.assertIsInstance(estrategia, PagamentoPix)

    def test_forma_invalida_levanta_excecao(self):
        with self.assertRaises(ValueError):
            obter_forma_pagamento("bitcoin")


class _ObservadorEspia(Observador):
    """Observador de teste que registra as chamadas recebidas."""

    def __init__(self):
        self.chamadas: list[tuple[int, str]] = []

    def atualizar(self, pedido_id: int, novo_status: str) -> None:
        self.chamadas.append((pedido_id, novo_status))


class TestesGerenciadorStatus(TestCase):

    def test_observador_registrado_e_notificado(self):
        gerenciador = GerenciadorStatus()
        espia = _ObservadorEspia()
        gerenciador.registrar(espia)

        gerenciador.notificar(pedido_id=42, novo_status="Pronto")

        self.assertEqual(espia.chamadas, [(42, "Pronto")])

    def test_observador_removido_nao_e_notificado(self):
        gerenciador = GerenciadorStatus()
        espia = _ObservadorEspia()
        gerenciador.registrar(espia)
        gerenciador.remover(espia)

        gerenciador.notificar(pedido_id=1, novo_status="Entregue")

        self.assertEqual(espia.chamadas, [])

    def test_multiplos_observadores_sao_todos_notificados(self):
        gerenciador = GerenciadorStatus()
        espia_1 = _ObservadorEspia()
        espia_2 = _ObservadorEspia()
        gerenciador.registrar(espia_1)
        gerenciador.registrar(espia_2)

        gerenciador.notificar(pedido_id=7, novo_status="Preparando")

        self.assertEqual(len(espia_1.chamadas), 1)
        self.assertEqual(len(espia_2.chamadas), 1)
