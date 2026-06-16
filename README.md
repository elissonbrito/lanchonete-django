# Lanchonete Django — Sistema de Pedidos

> **Prova Final — Engenharia de Software**
> Aplicação de Clean Code, SOLID, Design Patterns, TDD, BDD, Arquitetura Limpa, Microsserviços e Docker.

---

## 1. Descrição do problema e proposta da solução

Lanchonetes de pequeno porte enfrentam dificuldade em gerenciar pedidos simultâneos de balcão, mesa e entrega. Sem um sistema centralizado, erros de comunicação entre atendimento e cozinha geram atrasos, cobranças incorretas e insatisfação dos clientes.

**A solução proposta resolve:**

- Cálculo correto do total (com taxa de entrega para pedidos fora do estabelecimento)
- Suporte a três formas de pagamento: dinheiro, cartão e Pix
- Notificação automática da cozinha e do cliente a cada mudança de status
- Cardápio centralizado acessível a todos os pontos de atendimento
- Histórico de pedidos com acompanhamento de status em tempo real
- Painel administrativo para gestão completa do sistema

---

## 2. Divisão em microsserviços

O sistema é dividido em três microsserviços independentes, cada um com sua própria responsabilidade, banco de dados e ciclo de deploy:

```
lanchonete_ms/
├── servico_pedidos/        → Porta 8001 — criação e acompanhamento de pedidos
├── servico_cardapio/       → Porta 8002 — catálogo de produtos e preços
├── servico_notificacoes/   → Porta 8003 — registro e envio de notificações de status
└── gateway/                → Porta 80   — Nginx como API Gateway (roteamento)
```

Cada serviço tem seu próprio banco de dados (SQLite em dev, PostgreSQL em produção), pode ser implantado e escalado de forma independente e se comunica via HTTP REST.

**Por que microsserviços?** Permite que a equipe de cardápio atualize produtos sem afetar o serviço de pedidos. O serviço de notificações pode ser trocado por outro canal (e-mail, SMS) sem tocar nos demais.

---

## 3. Arquitetura Limpa — servico_pedidos

```
servico_pedidos/
├── dominio/                 ← Núcleo — zero dependência de framework
│   ├── entidades/
│   │   └── pedido.py        ← Entidades, enums e regras de negócio puras
│   ├── repositorios/
│   │   └── repositorio_pedido.py   ← Porta de saída (interface ABC)
│   └── servicos/
│       └── servico_pedido.py       ← Casos de uso + todos os padrões de projeto
├── infraestrutura/          ← Adaptadores — implementam as portas do domínio
│   ├── django_app/          ← Django como detalhe de infraestrutura
│   └── repositorios/        ← Implementação concreta de RepositorioPedido
├── interfaces/
│   └── http/                ← Views e controllers HTTP
└── testes/
    ├── unidade/             ← TDD — pytest puro, sem banco
    └── bdd/                 ← BDD — behave com Gherkin em português
```

**Regra de dependência:** camadas internas nunca importam camadas externas. O domínio não conhece Django, SQLite nem behave. Isso significa que toda a lógica de negócio pode ser testada sem subir nenhum servidor.

---

## 4. Princípios SOLID aplicados

| Princípio | Onde | Como |
|-----------|------|------|
| **SRP** — Responsabilidade Única | `servico_pedido.py` | Cada classe tem uma única razão para mudar: `EstrategiaPagamento` só trata pagamento; `GerenciadorNotificacoes` só notifica; `FabricaTipoPedido` só cria pedidos |
| **OCP** — Aberto/Fechado | `_estrategias` / `_tipos_pedido` | Novo pagamento ou tipo = nova classe + uma linha no dict. O código existente não muda |
| **LSP** — Substituição de Liskov | `EstrategiaPagamento`, `PedidoBase`, `ObservadorPedido` | Qualquer subclasse substitui a base sem quebrar o sistema. `PagamentoPix` pode substituir `PagamentoDinheiro` em qualquer contexto |
| **ISP** — Segregação de Interface | `RepositorioPedido` | Interface mínima com apenas `salvar`, `buscar_por_id` e `listar_recentes`. Sem métodos que clientes não precisam |
| **DIP** — Inversão de Dependência | `ServicoPedido` | Recebe `RepositorioPedido` (abstração) no construtor. Nunca instancia o banco diretamente. Nos testes, recebe um mock |

---

## 5. Design Patterns aplicados (4 implementados)

### Singleton — `ConfiguracaoLanchonete`

```python
class ConfiguracaoLanchonete:
    _instancia: "ConfiguracaoLanchonete | None" = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia.nome = "Lanchonete Django"
            cls._instancia.taxa_entrega = Decimal("5.00")
            cls._instancia.tempo_preparo_padrao_minutos = 20
        return cls._instancia
```

**Justificativa:** configurações globais devem existir em uma única instância durante toda a execução, evitando estados inconsistentes entre módulos.

---

### Strategy — `EstrategiaPagamento`

```python
class EstrategiaPagamento(ABC):
    @abstractmethod
    def processar(self, valor: Decimal) -> str: ...

class PagamentoPix(EstrategiaPagamento):
    def processar(self, valor: Decimal) -> str:
        return f"Pagamento de R${valor:.2f} via Pix confirmado."

# Nova forma: criar classe acima e adicionar uma linha aqui.
_estrategias: dict[FormaPagamento, type[EstrategiaPagamento]] = {
    FormaPagamento.DINHEIRO: PagamentoDinheiro,
    FormaPagamento.CARTAO:   PagamentoCartao,
    FormaPagamento.PIX:      PagamentoPix,
}
```

**Justificativa:** isola cada algoritmo de pagamento em sua própria classe. Adicionar boleto bancário = nova classe `PagamentoBoleto` + uma linha no dict, sem alterar nada existente.

---

### Factory Method — `FabricaTipoPedido`

```python
class FabricaTipoPedido:
    @staticmethod
    def criar(tipo: TipoPedido) -> PedidoBase:
        classe = _tipos_pedido.get(tipo)
        if classe is None:
            raise ValueError(f"Tipo '{tipo}' não registrado.")
        return classe()
```

**Justificativa:** desacopla a criação dos tipos de pedido do código que os usa. Adicionar `PedidoDrive` exige apenas uma nova classe e uma linha no dict, sem tocar na fábrica.

---

### Observer — `GerenciadorNotificacoes`

```python
class GerenciadorNotificacoes:
    def registrar(self, observador: ObservadorPedido) -> None:
        self._observadores.append(observador)

    def notificar(self, pedido_id: int, novo_status: str) -> None:
        for observador in self._observadores:
            observador.atualizar(pedido_id, novo_status)
```

**Justificativa:** desacopla o serviço de pedidos dos canais de notificação. Adicionar notificação por e-mail ou SMS = nova classe `ObservadorPedido`, sem tocar no restante do sistema.

---

## 6. Clean Code — evidências

- **Nomes revelam intenção:** `calcular_total`, `avancar_status`, `esta_finalizado`, `_obter_estrategia`, `_salvar_itens_do_pedido`
- **Funções pequenas com propósito único:** nenhuma função tem mais de 15 linhas
- **Sem comentários óbvios:** docstrings apenas em contratos de interface (`@abstractmethod`)
- **Sem números mágicos:** `TAXA_ENTREGA = Decimal("5.00")`, `StatusPedido.RECEBIDO`
- **Sem strings mágicas:** `TextChoices` no models.py para status, tipo e forma de pagamento
- **Early return:** validações no início das funções evitam aninhamento profundo
- **Tipos explícitos:** todas as assinaturas têm type hints (`-> Pedido`, `list[ItemPedido]`)
- **Português consistente:** código, variáveis, testes e arquivos de feature em português

---

## 7. TDD — testes unitários

```bash
# Executar os 25 testes
python -m pytest testes/unidade/teste_dominio_pedido.py -v
```

**25 testes passando**, cobrindo:

| Classe de teste | O que testa |
|-----------------|-------------|
| `TestesEntidadePedido` | Cálculo de total, avanço de status, estado finalizado, subtotal de item |
| `TestesEstrategiaPagamento` | Mensagens corretas das 3 formas de pagamento, presença do valor |
| `TestesFabricaTipoPedido` | Criação e taxas dos 3 tipos de pedido, erro para tipo inválido |
| `TestesGerenciadorNotificacoes` | Registro, remoção e notificação de observadores |
| `TestesConfiguracaoLanchonete` | Instância única, nome e taxa padrão |
| `TestesServicoPedido` | Criação de pedido com mock de repositório, mensagem de pagamento, erro para pedido inexistente |

**Ciclo aplicado em cada teste:**
1. **Red** — escrever o teste que falha
2. **Green** — escrever o mínimo de código para passar
3. **Refactor** — melhorar o código mantendo o teste verde

O mock de repositório isola completamente o domínio do banco de dados, tornando os testes rápidos (menos de 0,1s) e sem efeitos colaterais.

---

## 8. BDD — cenários de comportamento

```bash
# Executar os 4 cenários
behave testes/bdd/
```

**4 cenários passando** em `pedidos.feature`, escritos em Gherkin em português (`# language: pt`):

```gherkin
Funcionalidade: Criação de pedidos na lanchonete
  Como atendente da lanchonete
  Quero registrar pedidos dos clientes
  Para que a cozinha possa prepará-los e o cliente seja cobrado corretamente

  Cenário: Pedido de balcão com pagamento via Pix
    Dado que o cliente "João" quer fazer um pedido no balcão
    E o pedido contém o item "X-Burguer" que custa R$20,00
    Quando o cliente paga via "pix"
    Então o pedido deve ser criado com status "recebido"
    E o total do pedido deve ser R$20,00
    E a mensagem de pagamento deve mencionar "Pix"

  Cenário: Pedido de entrega com taxa adicional
    Dado que o cliente "Maria" quer fazer um pedido de entrega
    E o pedido contém o item "Suco" que custa R$10,00
    Quando o cliente paga via "cartao"
    Então o pedido deve ser criado com status "recebido"
    E o total do pedido deve ser R$15,00

  Cenário: Avanço do status do pedido
    Dado que existe um pedido com status "recebido"
    Quando o status do pedido avança
    Então o status do pedido deve ser "preparando"

  Cenário: Pedido entregue está finalizado
    Dado que existe um pedido com status "entregue"
    Então o pedido deve estar finalizado
```

Os cenários descrevem comportamento esperado do negócio, não detalhes técnicos. Qualquer pessoa — inclusive sem conhecimento de programação — consegue ler e validar os cenários.

---

## 9. Docker e Docker Compose

### Pré-requisitos

- Docker instalado: **docs.docker.com/get-docker**
- Docker Compose (já vem junto com o Docker Desktop no Windows e Mac)

**Linux:** instalar separadamente se necessário:
```bash
sudo apt install docker-compose-plugin
```

### Subir todos os serviços

Na raiz do projeto (`lanchonete_ms/`):

**Linux / Mac / Windows:**
```bash
docker compose up --build
```

Serviços disponíveis após subir:

| Serviço | Endereço |
|---------|----------|
| Interface principal | http://localhost |
| Serviço de pedidos | http://localhost:8001 |
| Serviço de cardápio | http://localhost:8002 |
| Serviço de notificações | http://localhost:8003 |

Para encerrar: `Ctrl+C` e depois:
```bash
docker compose down
```

Cada microsserviço tem seu próprio `Dockerfile`. O `docker-compose.yml` na raiz orquestra todos com rede interna, volumes persistentes e healthcheck.

---

## 10. Deploy no Render

### 1 — Subir o código no GitHub

**Linux / Mac / Windows:**
```bash
git init
git add .
git commit -m "lanchonete django - prova final"
git remote add origin https://github.com/SEU_USUARIO/lanchonete-django.git
git branch -M main
git push -u origin main
```

### 2 — Criar conta no Render

Acesse **render.com** e clique em **Continue with GitHub**.

### 3 — Criar o serviço

1. No dashboard, clique em **New → Blueprint**
2. Selecione o repositório `lanchonete-django`
3. O Render lê o arquivo `render.yaml` e configura tudo automaticamente
4. Clique em **Apply**

### 4 — Variáveis de ambiente

O `render.yaml` já configura tudo automaticamente, incluindo:

| Variável | Valor |
|----------|-------|
| `DJANGO_SECRET_KEY` | Gerada automaticamente pelo Render |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `.onrender.com,localhost` |
| `DATABASE_URL` | Gerada automaticamente pelo banco PostgreSQL |

### 5 — Após o deploy

O Render gera uma URL no formato:
```
https://lanchonete-pedidos.onrender.com
```

> **Atenção — plano gratuito:** o serviço dorme após 15 minutos sem acesso. Na primeira requisição após o sono ele demora cerca de 30 segundos para responder. Isso é normal no plano free.

---

## 11. Justificativas técnicas

| Decisão | Justificativa |
|---------|---------------|
| **Django como detalhe de infraestrutura** | O domínio (entidades, serviços) não importa Django. Permite trocar por FastAPI ou Flask sem reescrever as regras de negócio |
| **SQLite em dev, PostgreSQL em produção** | SQLite elimina dependências no desenvolvimento local; PostgreSQL oferece concorrência e durabilidade em produção |
| **Nginx como API Gateway** | Centraliza roteamento, permite SSL termination e balanceamento de carga sem alterar os serviços |
| **Behave com Gherkin em português** | Cenários legíveis por qualquer pessoa, não só desenvolvedores. Stakeholders podem validar sem conhecer código |
| **Mock de repositório nos testes** | Isola completamente o domínio do banco de dados, tornando os testes rápidos e sem efeitos colaterais |
| **Enums e TextChoices** | Elimina strings mágicas, oferece autocomplete e garante em tempo de execução que apenas valores válidos sejam usados |
| **Render para deploy** | Suporte nativo a Docker, PostgreSQL gerenciado, deploy automático via Git push, plano gratuito para avaliação |
| **WhiteNoise para arquivos estáticos** | Serve CSS e JS diretamente pelo Django em produção, sem precisar configurar Nginx ou S3 |

---

## Como executar localmente

### Pré-requisitos

- Python 3.10 ou superior
- Git

Para verificar se já está instalado:

**Linux / Mac:**
```bash
python3 --version
git --version
```

**Windows:**
```cmd
python --version
git --version
```

Caso não tenha Python, baixe em **python.org/downloads**. Marque a opção **"Add Python to PATH"** durante a instalação no Windows.

---

### 1 — Clonar o repositório

**Linux / Mac / Windows:**
```bash
git clone https://github.com/SEU_USUARIO/lanchonete-django.git
cd lanchonete-django
```

---

### 2 — Entrar na pasta do projeto Django

**Linux / Mac:**
```bash
cd lanchonete_ms/servico_pedidos/infraestrutura/django_app
```

**Windows:**
```cmd
cd lanchonete_ms\servico_pedidos\infraestrutura\django_app
```

---

### 3 — Criar o ambiente virtual

**Linux / Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

Quando o ambiente estiver ativo, você verá `(venv)` no início da linha do terminal.

---

### 4 — Instalar as dependências

**Linux / Mac / Windows:**
```bash
pip install -r ../../requirements.txt
```

---

### 5 — Preparar o banco de dados

**Linux / Mac / Windows:**
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py loaddata pedidos/fixtures/produtos_iniciais.json
python manage.py collectstatic --noinput
```

---

### 6 — Criar usuário administrador (opcional)

**Linux / Mac / Windows:**
```bash
python manage.py createsuperuser
```

Preencha usuário, e-mail e senha. O painel admin fica em **http://127.0.0.1:8000/admin**.

---

### 7 — Subir o servidor

**Linux / Mac / Windows:**
```bash
python manage.py runserver
```

Acesse no navegador: **http://127.0.0.1:8000**

Para encerrar o servidor: `Ctrl+C`

---

### 8 — Rodar os testes

Abra um segundo terminal, entre na pasta do projeto e ative o ambiente virtual novamente.

**Linux / Mac:**
```bash
cd lanchonete_ms/servico_pedidos
source infraestrutura/django_app/venv/bin/activate
```

**Windows:**
```cmd
cd lanchonete_ms\servico_pedidos
infraestrutura\django_app\venv\Scripts\activate
```

Depois rode os testes:

```bash
# Testes unitários (TDD) — 25 testes
python -m pytest testes/unidade/teste_dominio_pedido.py -v

# Cenários de comportamento (BDD) — 4 cenários
behave testes/bdd/
```

---

## Estrutura completa do projeto

```
lanchonete_ms/
├── servico_pedidos/
│   ├── dominio/
│   │   ├── entidades/
│   │   │   └── pedido.py             ← Entidades, enums e regras de negócio puras
│   │   ├── repositorios/
│   │   │   └── repositorio_pedido.py ← Interface ABC (porta de saída)
│   │   └── servicos/
│   │       └── servico_pedido.py     ← Casos de uso + Singleton, Strategy, Factory, Observer
│   ├── infraestrutura/
│   │   ├── django_app/
│   │   │   ├── lanchonete/
│   │   │   │   ├── settings.py       ← Configurações com variáveis de ambiente
│   │   │   │   ├── urls.py
│   │   │   │   └── wsgi.py
│   │   │   ├── pedidos/
│   │   │   │   ├── models.py         ← Models Django com TextChoices
│   │   │   │   ├── views.py          ← Views finas, delegam para services
│   │   │   │   ├── services.py       ← Camada de serviço (orquestra domínio)
│   │   │   │   ├── factory.py        ← Padrão Factory
│   │   │   │   ├── strategy.py       ← Padrão Strategy
│   │   │   │   ├── observer.py       ← Padrão Observer
│   │   │   │   ├── singleton.py      ← Padrão Singleton
│   │   │   │   ├── fixtures/         ← Dados iniciais (produtos)
│   │   │   │   ├── migrations/       ← Migrações do banco
│   │   │   │   └── templates/        ← HTML das páginas
│   │   │   └── manage.py
│   │   └── repositorios/             ← Implementação concreta do repositório
│   ├── interfaces/
│   │   └── http/                     ← Controllers HTTP
│   ├── testes/
│   │   ├── unidade/
│   │   │   └── teste_dominio_pedido.py  ← 25 testes TDD
│   │   └── bdd/
│   │       ├── pedidos.feature          ← 4 cenários Gherkin em português
│   │       └── steps/
│   │           └── passos_pedido.py     ← Implementação dos passos BDD
│   ├── Dockerfile
│   └── requirements.txt
├── servico_cardapio/                 ← Catálogo de produtos (porta 8002)
├── servico_notificacoes/             ← Notificações de status (porta 8003)
│   └── main.py                       ← Flask mínimo para receber eventos
├── gateway/
│   └── nginx.conf                    ← Roteamento via Nginx
├── docker-compose.yml                ← Orquestra todos os serviços
├── render.yaml                       ← Configuração de deploy no Render
├── .gitignore
└── README.md
```

---

> **Link de acesso ao sistema publicado:https://lanchonete-pedidos.onrender.com**
