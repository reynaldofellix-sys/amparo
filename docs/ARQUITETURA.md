# Arquitetura escalável

## Decisão principal

O AMPARO começa como um **monólito modular Django**. Essa forma reduz custo operacional e mantém transações consistentes, enquanto os módulos estabelecem fronteiras que podem ser separados quando volume e equipe justificarem.

```text
Navegador
   │ HTTPS
Load balancer / WAF
   │
Django stateless ───── Redis (cache, sessão e fila)
   │                         │
PostgreSQL primário       Celery workers
   │
réplicas de leitura / backup PITR
```

## Módulos

- `accounts`: identidade, credenciais, perfil e preferências;
- `banking`: conta demonstrativa, ledger, transferências e cartão;
- `core`: auditoria, assistente educativo e saúde da aplicação.

Views não alteram saldo diretamente. Regras financeiras ficam em serviços transacionais de domínio. O ledger é append-only pela aplicação, possui referência única e registra o saldo após cada lançamento.

## Consistência financeira

Ao confirmar uma transferência, o serviço:

1. inicia uma transação do banco;
2. bloqueia transferência e conta com `SELECT ... FOR UPDATE`;
3. verifica propriedade, status e saldo;
4. grava um único débito identificado pela chave de idempotência;
5. atualiza o saldo e conclui a transferência no mesmo commit;
6. agenda efeitos externos somente após o commit.

PostgreSQL é obrigatório em produção porque o SQLite não fornece o mesmo modelo de concorrência.

## Escala horizontal

- instâncias web não guardam estado em memória;
- sessões usam cache Redis com persistência no banco;
- arquivos estáticos são versionados e comprimidos pelo WhiteNoise, podendo migrar para CDN;
- tarefas lentas são enviadas ao Celery;
- health checks distintos cobrem processo e prontidão do banco;
- índices atendem histórico por conta, status e auditoria por usuário.

## Segurança

- CSRF, cookies `HttpOnly`/`Secure`, HSTS, `X-Frame-Options` e redirecionamento HTTPS em produção;
- senhas protegidas pelos hashers e validadores do Django;
- limitação de login pronta para Redis compartilhado;
- autorização por proprietário em todos os objetos financeiros;
- trilha de auditoria sem registrar chave Pix em eventos;
- segredos e conexões fornecidos por variáveis de ambiente.

Antes de produção real ainda são necessários: MFA/WebAuthn, gestão central de segredos, criptografia de campos sensíveis, SIEM, SAST/DAST, testes de intrusão, plano de incidentes, segregação de funções, KYC/AML e integração homologada com provedor financeiro.

## Evolução sem reescrita

Quando necessário, notificações, assistente e integração financeira podem sair do monólito por eventos transacionais. A contabilidade central deve permanecer em um único domínio de consistência até haver maturidade para um ledger dedicado.
