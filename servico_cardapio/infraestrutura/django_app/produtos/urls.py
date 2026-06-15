from django.urls import path
from . import views

urlpatterns = [
    path("produtos/", views.listar_produtos, name="listar_produtos"),
    path("produtos/<int:produto_id>/", views.detalhar_produto, name="detalhar_produto"),
    path("health/", views.health, name="health"),
]
