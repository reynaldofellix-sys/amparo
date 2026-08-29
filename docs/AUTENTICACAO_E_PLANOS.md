# Autenticação Google, planos e pagamentos

## Decisão técnica

O AMPARO usa `django-allauth` para autenticação Google por OpenID Connect e mantém a
autenticação tradicional por e-mail e senha. A integração solicita apenas os escopos
`openid`, `profile` e `email`.

O domínio de planos é independente da gateway. Usuários, planos e assinaturas ficam no
PostgreSQL, enquanto dados completos de cartão permanecem no provedor de pagamento.

A primeira gateway é o Mercado Pago. O código usa uma interface própria de provedor e pode
receber outro adaptador no futuro sem alterar as tabelas centrais.

## Fluxo de cadastro com Google

1. A pessoa seleciona **Continuar com Google**.
2. O Google confirma identidade, nome e e-mail.
3. O AMPARO cria a conta com uma senha inutilizável e não armazena o token do Google.
4. A pessoa completa nome, telefone, faixa etária, acessibilidade e consentimento.
5. Criar uma senha local é opcional; quem não criar continua entrando pelo Google.
6. Após o onboarding, a pessoa escolhe um plano.

Contas com onboarding pendente não acessam telas privadas nem a API. A API responde `409`
com `onboarding_required`, permitindo que um aplicativo móvel abra o fluxo correto.

## Configuração Google

Crie um cliente OAuth do tipo **Aplicativo da Web** no Google Cloud e configure:

- origem local: `http://127.0.0.1:8000`;
- callback local: `http://127.0.0.1:8000/autenticacao/google/login/callback/`;
- callback de produção: `https://SEU-DOMINIO/autenticacao/google/login/callback/`.

Variáveis:

```env
GOOGLE_OAUTH_CLIENT_ID=seu-client-id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=seu-client-secret
```

Use projetos Google separados para desenvolvimento e produção. A página inicial e a política
de privacidade precisam permanecer públicas no domínio de produção.

Documentação oficial:

- https://developers.google.com/identity/openid-connect/openid-connect
- https://docs.allauth.org/en/latest/socialaccount/providers/google.html

## Planos

Três planos iniciais são criados por migração:

- **Gratuito** — ativo imediatamente, sem gateway;
- **Cuidado** — R$ 14,90/mês;
- **Família** — R$ 29,90/mês.

Os valores são iniciais e podem ser alterados no Django Admin. Os planos pagos permanecem
bloqueados para cobrança até que um `mercado_pago_plan_id` seja cadastrado explicitamente.
Isso impede cobranças acidentais durante o desenvolvimento.

## Configuração Mercado Pago

1. Crie uma conta de vendedor e uma aplicação em **Suas integrações**.
2. Crie os planos recorrentes no Mercado Pago.
3. Copie o identificador de cada plano para `mercado_pago_plan_id` no Django Admin.
4. Configure as credenciais abaixo.
5. Cadastre o webhook de assinaturas apontando para
   `https://SEU-DOMINIO/webhooks/mercado-pago/`.
6. Teste com as credenciais de teste antes de ativar produção.

```env
PUBLIC_BASE_URL=https://SEU-DOMINIO
PAYMENT_PROVIDER=mercado_pago
MERCADO_PAGO_ACCESS_TOKEN=APP_USR-...
MERCADO_PAGO_WEBHOOK_SECRET=...
```

O webhook valida `x-signature` por HMAC, consulta novamente a assinatura na API oficial e
processa cada evento uma única vez. Nunca libera um plano apenas com os dados enviados no
corpo do webhook.

Documentação oficial:

- https://www.mercadopago.com.br/developers/pt/docs/subscriptions/overview
- https://www.mercadopago.com.br/developers/pt/docs/your-integrations/notifications/webhooks

## Custos

Google Sign-In não exige uma cobrança por login. Mercado Pago não cobra custo fixo para
começar a vender, mas cobra tarifas em vendas aprovadas. As taxas variam por meio de pagamento
e prazo de recebimento e devem ser confirmadas no painel antes da publicação.

Não existe gateway completa sem tarifa de transação. O plano Gratuito do AMPARO não chama a
gateway e, portanto, não gera custo de pagamento.

## Segurança operacional

- segredos somente em variáveis de ambiente;
- nenhuma credencial no Git;
- nenhum dado completo de cartão no AMPARO;
- checkout hospedado pela gateway;
- idempotência na criação e nos webhooks;
- apenas uma assinatura aberta por usuário;
- troca de plano pago bloqueada até o cancelamento da assinatura atual;
- HTTPS obrigatório em produção.
