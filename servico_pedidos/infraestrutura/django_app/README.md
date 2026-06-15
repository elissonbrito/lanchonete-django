# 🍔 Lanchonete Django — Padrões de Projeto

Projeto desenvolvido para a disciplina de **Arquitetura de Software**.  
Sistema simples de pedidos de lanchonete que demonstra **4 padrões de projeto** integrados.

---

## ▶️ Como rodar o projeto

```bash
# 1. Instalar o Django
pip install django

# 2. Entrar na pasta do projeto
cd lanchonete

# 3. Aplicar as migrações (cria o banco de dados)
python manage.py migrate

# 4. Carregar produtos iniciais
python manage.py loaddata pedidos/fixtures/produtos_iniciais.json

# 5. Criar usuário admin (para acessar /admin/)
python manage.py createsuperuser

# 6. Rodar o servidor
python manage.py runserver
```

Acesse: http://127.0.0.1:8000

---

## 📐 Padrões de Projeto Utilizados

### 1. Singleton — `pedidos/singleton.py`
**Categoria:** Criacional

**Problema:** As configurações da lanchonete (nome, taxa de entrega, tempo médio)
precisam ser únicas e consistentes em toda a aplicação.

**Solução:** A classe `ConfiguracaoLanchonete` usa `__new__` para garantir que
**uma única instância** seja criada. Todas as chamadas posteriores retornam
o mesmo objeto já inicializado.

```python
config1 = ConfiguracaoLanchonete()
config2 = ConfiguracaoLanchonete()
assert config1 is config2  # True — é o mesmo objeto!
```

---

### 2. Factory Method — `pedidos/factory.py`
**Categoria:** Criacional

**Problema:** Existem 3 tipos de pedido com comportamentos diferentes:
- **Balcão:** sem taxa adicional
- **Entrega:** adiciona R$5,00 de taxa
- **Mesa:** sem taxa, mas com número de mesa

Sem Factory, o código teria `if/elif` espalhado em vários lugares.

**Solução:** A `FabricaPedido.criar()` centraliza a criação e retorna o objeto certo:

```python
pedido = FabricaPedido.criar(tipo="entrega", itens=[...], cliente="João")
total = pedido.calcular_total(30.00)  # → 35.00 (com taxa)
```

---

### 3. Observer — `pedidos/observer.py`
**Categoria:** Comportamental

**Problema:** Quando o status de um pedido muda, múltiplos sistemas precisam
ser avisados (cozinha, cliente). Se acoplarmos isso diretamente às views,
fica difícil adicionar novos observadores.

**Solução:** O `GerenciadorStatus` mantém uma lista de observadores.
Ao chamar `notificar_todos()`, cada observador reage automaticamente:

```python
gerenciador_status.registrar(NotificadorCozinha())
gerenciador_status.registrar(NotificadorCliente())

# Quando o status muda:
gerenciador_status.notificar_todos(pedido_id=1, novo_status="Pronto")
# → [COZINHA] Pedido #1 agora está: Pronto
# → [CLIENTE] Seu pedido #1 está: Pronto
```

---

### 4. Strategy — `pedidos/strategy.py`
**Categoria:** Comportamental

**Problema:** Cada forma de pagamento (Dinheiro, Cartão, Pix) tem seu próprio
processamento. Usar `if pagamento == "pix"` viola o princípio Aberto/Fechado.

**Solução:** Cada forma é uma classe separada com o mesmo método `processar()`.
A função `obter_forma_pagamento()` seleciona a estratégia certa:

```python
estrategia = obter_forma_pagamento("pix")
msg = estrategia.processar(35.00)
# → "Pagamento de R$35.00 via PIX confirmado."
```

---

## 🗂️ Estrutura do Projeto

```
lanchonete/
├── manage.py
├── lanchonete/
│   ├── settings.py
│   └── urls.py
└── pedidos/
    ├── models.py          # Produto, Pedido, ItemPedido
    ├── views.py           # Integra os 4 padrões
    ├── urls.py            # Rotas
    ├── singleton.py       # Padrão 1: Singleton
    ├── factory.py         # Padrão 2: Factory Method
    ├── observer.py        # Padrão 3: Observer
    ├── strategy.py        # Padrão 4: Strategy
    ├── admin.py
    ├── fixtures/
    │   └── produtos_iniciais.json
    └── templates/pedidos/
        ├── base.html
        ├── home.html
        ├── novo_pedido.html
        └── sobre_padroes.html
```

---

## 🎥 Roteiro sugerido para o vídeo (5–10 min)

1. **(1 min)** Apresentar o problema: sistema de pedidos de lanchonete
2. **(1 min)** Mostrar a estrutura de arquivos e a arquitetura geral
3. **(6 min)** Abrir cada arquivo de padrão, explicar o problema e a solução:
   - `singleton.py` → mostrar o `__new__` e provar que é a mesma instância
   - `factory.py` → mostrar as classes e o método `criar()`
   - `observer.py` → mostrar `registrar()` e `notificar_todos()`
   - `strategy.py` → mostrar a interface e as classes concretas
4. **(1 min)** Demonstrar o sistema rodando no navegador
5. **(1 min)** Benefícios: organização, facilidade de adicionar novos tipos/pagamentos/observadores

---

## 🔑 Acesso ao Admin

- URL: http://127.0.0.1:8000/admin/
- Usuário: `admin`
- Senha: `admin123`

Use o admin para cadastrar mais produtos ou visualizar pedidos.
