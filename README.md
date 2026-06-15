# Lanchonete Django — Sistema de Pedidos

> **Prova Final — Engenharia de Software**
> Aplicação de Clean Code, SOLID, Design Patterns, TDD, BDD, Arquitetura Limpa, Microsserviços e Docker.

---

## 1. Descrição do Problema

Lanchonetes de médio porte enfrentam dificuldade em gerenciar pedidos simultâneos de balcão, mesa e entrega. O sistema precisa calcular totais corretamente (com ou sem taxa de entrega), aceitar diferentes formas de pagamento, notificar a cozinha e o cliente sobre mudanças de status, e manter um cardápio centralizado acessível a todos os pontos de atendimento.

---

## 2. Divisão em Microsserviços

```
lanchonete_ms/
├── servico_pedidos/        → Porta 8001 — criação e acompanhamento de pedidos
├── servico_cardapio/       → Porta 8002 — catálogo de produtos e preços
├── servico_notificacoes/   → Porta 8003 — registro e envio de notificações de status
└── gateway/                → Porta 80   — Nginx como API Gateway (roteamento)
```

Cada serviço tem seu próprio banco de dados (SQLite em dev, PostgreSQL em produção), pode ser implantado e escalado de forma independente e se comunica via HTTP REST.

---

## 3. Arquitetura Limpa — servico_pedidos

```
servico_pedidos/
├── dominio/                 ← Núcleo — zero dependência de framework
│   ├── entidades/
│   │   └── pedido.py        ← Entidades e enums do domínio
│   ├── repositorios/
│   │   └── repositorio_pedido.py   ← Porta de saída (interface ABC)
│   └── servicos/
│       └── servico_pedido.py       ← Casos de uso + todos os padrões
├── infraestrutura/          ← Adaptadores — implementam as portas do domínio
│   ├── django_app/          ← Django como detalhe de infraestrutura
│   └── repositorios/        ← Implementação concreta de RepositorioPedido
├── interfaces/
│   └── http/                ← Views/controllers HTTP
└── testes/
    ├── unidade/             ← TDD — pytest puro, sem banco
    └── bdd/                 ← BDD — behave com Gherkin em português
```

**Regra de dependência:** camadas internas nunca importam camadas externas. O domínio não conhece Django, SQLite nem behave.

---

## 4. Princípios SOLID Aplicados

| Princípio | Onde | Como |
|-----------|------|------|
| **SRP** | `servico_pedido.py` | Cada classe tem uma única razão para mudar: `EstrategiaPagamento` só trata pagamento; `GerenciadorNotificacoes` só notifica |
| **OCP** | `_estrategias` / `_tipos_pedido` | Novo pagamento ou tipo = nova classe + uma linha no dict. Código existente não muda |
| **LSP** | `EstrategiaPagamento`, `PedidoBase`, `ObservadorPedido` | Qualquer subclasse pode substituir a base sem quebrar quem a usa |
| **ISP** | `RepositorioPedido` | Interface mínima: `salvar`, `buscar_por_id`, `listar_recentes`. Sem métodos que clientes não precisam |
| **DIP** | `ServicoPedido` | Recebe `RepositorioPedido` (abstração) no construtor. Nunca instancia o banco diretamente |

---

## 5. Design Patterns Aplicados (4 mínimo — 4 implementados)

### Singleton — `ConfiguracaoLanchonete`
```python
class ConfiguracaoLanchonete:
    _instancia: "ConfiguracaoLanchonete | None" = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia.nome = "Lanchonete Django"
            cls._instancia.taxa_entrega = Decimal("5.00")
        return cls._instancia
```
**Justificativa:** configurações globais devem existir em uma única instância para evitar estados inconsistentes entre módulos.

---

### Strategy — `EstrategiaPagamento`
```python
class EstrategiaPagamento(ABC):
    @abstractmethod
    def processar(self, valor: Decimal) -> str: ...

class PagamentoPix(EstrategiaPagamento):
    def processar(self, valor: Decimal) -> str:
        return f"Pagamento de R${valor:.2f} via Pix confirmado."

# Registro centralizado — OCP: nova forma = nova classe + uma linha aqui
_estrategias: dict[FormaPagamento, type[EstrategiaPagamento]] = {
    FormaPagamento.DINHEIRO: PagamentoDinheiro,
    FormaPagamento.CARTAO:   PagamentoCartao,
    FormaPagamento.PIX:      PagamentoPix,
}
```
**Justificativa:** isola cada algoritmo de pagamento em sua própria classe, permitindo adicionar novos métodos sem alterar o código existente.

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
**Justificativa:** desacopla a criação dos tipos de pedido do código que os usa. Adicionar `PedidoDrive` exige apenas uma nova classe e uma linha no dict.

---

### Observer — `GerenciadorNotificacoes`
```python
class GerenciadorNotificacoes:
    def registrar(self, observador: ObservadorPedido) -> None: ...
    def remover(self, observador: ObservadorPedido) -> None: ...
    def notificar(self, pedido_id: int, novo_status: str) -> None:
        for observador in self._observadores:
            observador.atualizar(pedido_id, novo_status)
```
**Justificativa:** desacopla o serviço de pedidos dos canais de notificação. Adicionar notificação por e-mail ou SMS = nova classe `ObservadorPedido`, sem tocar no restante.

---

## 6. Clean Code — Evidências

- **Nomes revelam intenção:** `calcular_total`, `avancar_status`, `esta_finalizado`, `_obter_estrategia`
- **Funções pequenas e com propósito único:** nenhuma função tem mais de 15 linhas
- **Sem comentários óbvios:** docstrings apenas em contratos de interface (`@abstractmethod`)
- **Sem números mágicos:** `TAXA_ENTREGA = Decimal("5.00")`, `StatusPedido.RECEBIDO`
- **Early return:** validações no início das funções evitam aninhamento profundo
- **Tipos explícitos:** todas as assinaturas têm type hints (`-> Pedido`, `list[ItemPedido]`)
- **Português consistente:** código, variáveis, testes e arquivos de feature em português

---

## 7. TDD — Testes Unitários

```bash
# Executar
cd servico_pedidos
python -m pytest testes/unidade/ -v
```

**25 testes passando**, cobrindo:

- `TestesEntidadePedido` — cálculo de total, avanço de status, estado finalizado
- `TestesEstrategiaPagamento` — mensagens das 3 formas de pagamento
- `TestesFabricaTipoPedido` — criação e taxas dos 3 tipos
- `TestesGerenciadorNotificacoes` — registro, remoção e notificação de observadores
- `TestesConfiguracaoLanchonete` — instância única, valores padrão
- `TestesServicoPedido` — criação via mock de repositório (isola banco)

Ciclo aplicado: **Red → Green → Refactor** em cada teste.

---

## 8. BDD — Cenários de Comportamento

```bash
# Executar
cd servico_pedidos
behave testes/bdd/
```

**4 cenários passando** em `pedidos.feature`:

```gherkin
Cenário: Pedido de balcão com pagamento via Pix
  Dado que o cliente "João" quer fazer um pedido no balcão
  E o pedido contém o item "X-Burguer" que custa R$20,00
  Quando o cliente paga via "pix"
  Então o pedido deve ser criado com status "recebido"
  E o total do pedido deve ser R$20,00
  E a mensagem de pagamento deve mencionar "Pix"
```

Os cenários estão escritos em Gherkin em português (`# language: pt`) e descrevem comportamento esperado do negócio, não detalhes técnicos.

---

## 9. Docker e Docker Compose

```bash
# Subir todos os serviços
docker compose up --build

# Acessar
# Interface principal:    http://localhost
# Serviço de pedidos:     http://localhost:8001
# Serviço de cardápio:    http://localhost:8002
# Serviço de notificações: http://localhost:8003
```

Cada microsserviço tem seu próprio `Dockerfile`. O `docker-compose.yml` na raiz orquestra todos com rede interna, volumes persistentes e healthcheck.

---

## 10. Deploy em Servidor (Railway)

### Passo a passo para deploy no Railway

```bash
# 1. Instalar Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Criar projeto
railway init

# 4. Deploy de cada serviço
cd servico_pedidos && railway up
cd servico_cardapio && railway up
cd servico_notificacoes && railway up
```

### Variáveis de ambiente necessárias (Railway Dashboard)

```
DJANGO_SECRET_KEY=<gerar com: python -c "import secrets; print(secrets.token_hex(50))">
DEBUG=False
ALLOWED_HOSTS=<dominio-railway>.up.railway.app
DATABASE_URL=<gerado automaticamente pelo Railway PostgreSQL>
```

### Alternativa: Render.com

```yaml
# render.yaml
services:
  - type: web
    name: lanchonete-pedidos
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python infraestrutura/django_app/manage.py runserver 0.0.0.0:$PORT
    envVars:
      - key: DJANGO_SECRET_KEY
        generateValue: true
      - key: DEBUG
        value: false
```

> **Link de acesso:** após o deploy, o Railway gera um URL no formato `https://lanchonete-pedidos-production.up.railway.app`. Inserir aqui após publicação.

---

## 11. Justificativas Técnicas

| Decisão | Justificativa |
|---------|---------------|
| **Django como detalhe de infraestrutura** | O domínio (entidades, serviços) não importa Django. Isso permite trocar por FastAPI ou Flask sem reescrever regras de negócio |
| **SQLite em dev, PostgreSQL em produção** | SQLite elimina dependências no desenvolvimento local; PostgreSQL oferece concorrência e durabilidade em produção |
| **Nginx como Gateway** | Centraliza roteamento, permite SSL termination e balanceamento de carga sem alterar os serviços |
| **Behave com Gherkin em português** | Features em linguagem natural em português permitem que stakeholders validem os cenários sem conhecer código |
| **Mock de repositório nos testes** | Isola completamente o domínio do banco de dados, tornando os testes rápidos (< 0,1s) e sem efeitos colaterais |
| **Enums para status/tipo/pagamento** | Elimina strings mágicas, oferece autocomplete e garante em tempo de execução que apenas valores válidos sejam usados |
| **Railway para deploy** | Suporte nativo a Docker, PostgreSQL gerenciado, deploy automático via Git push, plano gratuito para avaliação |

---

## Executar localmente sem Docker

```bash
# Clonar e entrar no serviço principal
cd servico_pedidos

# Instalar dependências
pip install -r requirements.txt

# Rodar testes TDD
python -m pytest testes/unidade/ -v

# Rodar cenários BDD
behave testes/bdd/

# Subir servidor
python infraestrutura/django_app/manage.py migrate
python infraestrutura/django_app/manage.py runserver
```
