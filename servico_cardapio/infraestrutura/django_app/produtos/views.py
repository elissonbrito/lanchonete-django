import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import Produto


@require_http_methods(["GET"])
def listar_produtos(request):
    categoria = request.GET.get("categoria")
    busca = request.GET.get("busca")

    produtos = Produto.objects.filter(disponivel=True)
    if categoria:
        produtos = produtos.filter(categoria=categoria)
    if busca:
        produtos = produtos.filter(nome__icontains=busca)

    dados = [
        {
            "id": p.id,
            "nome": p.nome,
            "descricao": p.descricao,
            "preco": str(p.preco),
            "categoria": p.categoria,
        }
        for p in produtos
    ]
    return JsonResponse(dados, safe=False)


@require_http_methods(["GET"])
def detalhar_produto(request, produto_id):
    try:
        produto = Produto.objects.get(pk=produto_id, disponivel=True)
    except Produto.DoesNotExist:
        return JsonResponse({"erro": "Produto não encontrado."}, status=404)

    return JsonResponse({
        "id": produto.id,
        "nome": produto.nome,
        "descricao": produto.descricao,
        "preco": str(produto.preco),
        "categoria": produto.categoria,
    })


@require_http_methods(["GET"])
def health(request):
    return JsonResponse({"status": "ok", "servico": "cardapio"})
