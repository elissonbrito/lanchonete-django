from django.db import models


class CategoriaProduto(models.TextChoices):
    LANCHE = "lanche", "Lanche"
    BEBIDA = "bebida", "Bebida"
    SOBREMESA = "sobremesa", "Sobremesa"
    ACOMPANHAMENTO = "acompanhamento", "Acompanhamento"


class Produto(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    preco = models.DecimalField(max_digits=6, decimal_places=2)
    categoria = models.CharField(
        max_length=20,
        choices=CategoriaProduto.choices,
        default=CategoriaProduto.LANCHE,
    )
    disponivel = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ["categoria", "nome"]

    def __str__(self) -> str:
        return f"{self.nome} — R${self.preco:.2f}"
