from django.db import models


class StatusPedido(models.TextChoices):
    RECEBIDO = "recebido", "Recebido"
    PREPARANDO = "preparando", "Preparando"
    PRONTO = "pronto", "Pronto"
    ENTREGUE = "entregue", "Entregue"


class TipoPedido(models.TextChoices):
    BALCAO = "balcao", "Balcão"
    ENTREGA = "entrega", "Entrega"
    MESA = "mesa", "Mesa"


class OpcaoPagamento(models.TextChoices):
    DINHEIRO = "dinheiro", "Dinheiro"
    CARTAO = "cartao", "Cartão"
    PIX = "pix", "Pix"


class Produto(models.Model):
    nome = models.CharField(max_length=100)
    preco = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ["nome"]

    def __str__(self) -> str:
        return f"{self.nome} — R${self.preco:.2f}"


class Pedido(models.Model):
    cliente = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TipoPedido.choices, default=TipoPedido.BALCAO)
    status = models.CharField(max_length=20, choices=StatusPedido.choices, default=StatusPedido.RECEBIDO)
    forma_pagamento = models.CharField(max_length=20, choices=OpcaoPagamento.choices, default=OpcaoPagamento.DINHEIRO)
    numero_mesa = models.IntegerField(null=True, blank=True)
    total = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    criado_em = models.DateTimeField(auto_now_add=True)
    produtos = models.ManyToManyField(Produto, through="ItemPedido")

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ["-criado_em"]

    def __str__(self) -> str:
        return f"Pedido #{self.pk} — {self.cliente}"


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="itens")
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Item do Pedido"
        verbose_name_plural = "Itens do Pedido"

    @property
    def subtotal(self):
        return self.produto.preco * self.quantidade

    def __str__(self) -> str:
        return f"{self.quantidade}x {self.produto.nome} (Pedido #{self.pedido_id})"
