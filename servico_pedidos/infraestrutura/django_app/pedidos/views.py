from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .models import Pedido, Produto
from .services import atualizar_status_pedido, processar_novo_pedido
from .singleton import ConfiguracaoLanchonete


def pagina_inicial(request):
    configuracao = ConfiguracaoLanchonete()
    pedidos_recentes = Pedido.objects.order_by("-criado_em")[:10]
    return render(request, "pedidos/home.html", {
        "config": configuracao,
        "pedidos": pedidos_recentes,
    })


def novo_pedido(request):
    produtos = Produto.objects.all()

    if request.method == "GET":
        return render(request, "pedidos/novo_pedido.html", {"produtos": produtos})

    nome_cliente = request.POST.get("cliente", "").strip()
    ids_produtos = request.POST.getlist("produtos")

    if not nome_cliente or not ids_produtos:
        messages.error(request, "Preencha o nome e selecione ao menos um produto.")
        return render(request, "pedidos/novo_pedido.html", {"produtos": produtos})

    pedido, mensagem_pagamento = processar_novo_pedido(
        cliente=nome_cliente,
        tipo=request.POST.get("tipo"),
        forma_pagamento=request.POST.get("forma_pagamento"),
        numero_mesa=request.POST.get("numero_mesa") or None,
        ids_produtos=ids_produtos,
    )

    messages.success(request, f"Pedido #{pedido.pk} criado! {mensagem_pagamento}")
    return redirect("home")


def atualizar_status(request, pedido_id: int):
    pedido = get_object_or_404(Pedido, pk=pedido_id)

    if request.method != "POST":
        return redirect("home")

    novo_status = request.POST.get("status")
    atualizar_status_pedido(pedido, novo_status)

    messages.success(request, f"Status do pedido #{pedido_id} atualizado para '{novo_status}'.")
    return redirect("home")


def sobre_padroes(request):
    configuracao = ConfiguracaoLanchonete()
    return render(request, "pedidos/sobre_padroes.html", {"config": configuracao})
