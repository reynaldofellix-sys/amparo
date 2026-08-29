# AMPARO

Plataforma acadêmica de inclusão e educação financeira, construída em Django e preparada para PostgreSQL. O foco é oferecer uma experiência clara, acessível e segura para idosos, jovens e pessoas com pouca familiaridade com serviços financeiros.

> **Importante:** o AMPARO não é uma instituição financeira. Transferências, saldos, contas e cartões deste repositório são exclusivamente demonstrativos e não movimentam dinheiro real.

## O que já funciona

- cadastro e autenticação por e-mail, com senhas protegidas pelo Django;
- limitação distribuível de tentativas de login;
- perfil, faixa etária e preferência de texto ampliado;
- conta demonstrativa e ledger de lançamentos imutáveis;
- transferência em duas etapas com transação atômica, bloqueio de linha e idempotência;
- histórico paginado de movimentações;
- solicitação demonstrativa de cartão;
- preferências de alertas, confirmação e acessibilidade;
- assistente educativo com histórico privado por usuário;
- auditoria de eventos relevantes;
- health checks, PostgreSQL, Redis, Celery e configuração de produção;
- painel administrativo e suíte automatizada de testes;
- identidade visual própria, controles de texto/contraste e interface mobile-first;
- PWA instalável e API de leitura versionada em `/api/v1/` para um futuro aplicativo;
- login Google com onboarding seguro e senha local opcional;
- planos próprios, assinatura gratuita e integração desacoplada com Mercado Pago;
- webhooks assinados, idempotentes e conferidos novamente na API da gateway.

## Executar localmente

### Ambiente Python

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements/development.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Acesse `http://127.0.0.1:8000`. A conta acadêmica criada pelo comando é:

- e-mail: `demo@amparo.local`
- senha: `AmparoDemo2026!`

O desenvolvimento local usa SQLite por conveniência. O ambiente de produção exige PostgreSQL.

### PostgreSQL e Redis

Instale os serviços diretamente no servidor ou utilize provedores gerenciados. Copie `.env.example` para `.env` e ajuste `DATABASE_URL`, `REDIS_URL`, `CACHE_URL`, hosts, origens confiáveis e `DJANGO_SECRET_KEY` antes de publicar.

## Qualidade

```powershell
ruff check .
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test --settings=amparo.settings.test
coverage run manage.py test --settings=amparo.settings.test
coverage report
```

## Estrutura

```text
amparo/                 configuração, URLs, ASGI/WSGI e Celery
apps/accounts/          identidade, perfil, autenticação e preferências
apps/banking/           conta, ledger, transferências e cartão
apps/core/              auditoria, assistente e health checks
apps/subscriptions/     planos, assinaturas, gateway e webhooks
templates/              interface Django renderizada no servidor
static/                 CSS e JavaScript progressivamente aprimorado
docs/                   proposta, arquitetura e evolução do produto
```

Leia [a proposta](docs/PROPOSTA.md), [a arquitetura](docs/ARQUITETURA.md), [a identidade visual](docs/IDENTIDADE_VISUAL.md), [a preparação mobile](docs/APP_MOBILE.md), [a autenticação e os planos](docs/AUTENTICACAO_E_PLANOS.md), [a operação em produção](docs/producao.md) e [o roadmap](docs/ROADMAP.md) antes de ampliar o sistema.
