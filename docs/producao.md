# Produção do AMPARO

## Arquitetura publicada

- domínio: `amparo.nabio.pro`;
- servidor: Ubuntu 22.04;
- aplicação: Django + Gunicorn;
- proxy e TLS: Nginx + Certbot;
- banco: PostgreSQL local, banco `amparo_prod`, usuário `amparo_app`;
- cache e sessões: Redis local, banco lógico exclusivo;
- serviço: `amparo.service`, executado pelo usuário de sistema `amparo`;
- porta interna: `127.0.0.1:8050`, nunca exposta no firewall;
- código: releases imutáveis identificadas pelo hash do commit publicado no GitHub.

## Diretórios

```text
/var/www/apps/amparo/
├── current -> releases/AAAAmmdd-HHMMSS-COMMIT
├── releases/
├── shared/
│   ├── .env
│   ├── acme/
│   ├── media/
│   ├── staticfiles/
│   ├── logs/
│   └── backups/
└── venv/
```

O arquivo `.env` tem modo `0640`, pertence a `root:amparo` e nunca é versionado. Os
diretórios compartilhados pertencem ao usuário `amparo`. O Nginx recebe somente leitura em
`media` e `staticfiles` por meio do grupo `www-data` e das permissões de diretório.

## Variáveis obrigatórias

```env
DJANGO_SETTINGS_MODULE=amparo.settings.production
DJANGO_SECRET_KEY=
DJANGO_ALLOWED_HOSTS=amparo.nabio.pro,127.0.0.1,localhost
DJANGO_CSRF_TRUSTED_ORIGINS=https://amparo.nabio.pro
DJANGO_SECURE_SSL_REDIRECT=true
DJANGO_SECURE_HSTS_SECONDS=31536000
DATABASE_URL=postgresql://amparo_app:SENHA@127.0.0.1:5432/amparo_prod
DATABASE_CONN_MAX_AGE=0
DATABASE_POOL=true
REDIS_URL=redis://127.0.0.1:6379/10
CACHE_URL=redis://127.0.0.1:6379/11
PUBLIC_BASE_URL=https://amparo.nabio.pro
PAYMENT_PROVIDER=mercado_pago
```

Ao usar o pool nativo do `psycopg`, mantenha `DATABASE_CONN_MAX_AGE=0`: o pool já gerencia o
reaproveitamento das conexões e não pode ser combinado com conexões persistentes do Django.

Google OAuth e Mercado Pago permanecem desativados até que suas credenciais reais sejam
adicionadas no `.env`. Nunca coloque segredos no Git ou na unidade systemd.

## Processo de atualização

1. Faça a alteração local e adicione ou atualize os testes correspondentes.
2. Execute lint, suíte completa, cobertura, migrations check e `check --deploy`.
3. Faça commit e push; confirme que o hash existe em `origin/main`.
4. Crie uma release nova a partir exatamente desse hash.
5. Antes de migrations, gere em `shared/backups` um `pg_dump` com data, hora e commit.
6. Instale dependências no `venv` exclusivo e registre `pip freeze` na release.
7. Aponte `staticfiles` e `media` da release para os diretórios compartilhados.
8. Execute `migrate`, `collectstatic --noinput` e `check --deploy` com o `.env` de produção.
9. Troque o link `current` atomicamente e reinicie somente `amparo.service`.
10. Valide porta interna, domínio, HTTPS, logs e os demais projetos.

Nunca edite código diretamente em `current` ou numa release. Uma correção começa no GitHub e
gera outra release.

## Backup e rollback

Backup antes de migrations:

```bash
sudo -u postgres pg_dump -Fc amparo_prod > \
  /var/www/apps/amparo/shared/backups/amparo_DATA_HORA_COMMIT.dump
```

Rollback de código:

1. identifique a release anterior compatível;
2. aponte `current` novamente para essa release com um link simbólico temporário e renomeação
   atômica;
3. reinicie somente `amparo.service`;
4. execute os health checks interno e público;
5. restaure o banco apenas se a migration não for retrocompatível e houver decisão explícita.

Mantenha no mínimo as duas releases mais recentes. Não apague backups automaticamente sem uma
política de retenção aprovada.

## Operação e diagnóstico

```bash
systemctl status amparo.service
journalctl -u amparo.service --no-pager -n 100
tail -n 100 /var/www/apps/amparo/shared/logs/gunicorn-error.log
curl --fail http://127.0.0.1:8050/health/live/
curl --fail http://127.0.0.1:8050/health/ready/
curl --fail https://amparo.nabio.pro/health/ready/
nginx -t
certbot certificates
certbot renew --dry-run
```

Em emergência, preserve evidências, não reinicie outros serviços e não libere a porta 8050 no
firewall. Se o processo falhar, consulte primeiro o journal e os logs exclusivos do AMPARO.

## TLS

O desafio ACME usa `/var/www/apps/amparo/shared/acme`. A configuração HTTP fica em
`deploy/nginx-amparo-http`; após a emissão do certificado, aplique
`deploy/nginx-amparo-https`. Só habilite HSTS após validar certificado, redirecionamento e
health checks HTTPS. A renovação deve ser confirmada com `certbot renew --dry-run`.
