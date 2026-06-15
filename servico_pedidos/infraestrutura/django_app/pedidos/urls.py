from django.urls import path
from . import views

urlpatterns = [
    path("", views.pagina_inicial, name="home"),
    path("novo/", views.novo_pedido, name="novo_pedido"),
    path("status/<int:pedido_id>/", views.atualizar_status, name="atualizar_status"),
    path("padroes/", views.sobre_padroes, name="sobre_padroes"),
]
