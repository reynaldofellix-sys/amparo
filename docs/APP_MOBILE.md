# Preparação para aplicativo móvel

## PWA atual

O projeto contém manifesto instalável, identidade maskable, navegação respeitando áreas seguras do aparelho e um service worker conservador. Somente o shell visual e a página de indisponibilidade podem ser armazenados em cache; páginas autenticadas e informações financeiras continuam dependentes da rede.

## API versionada

As primeiras rotas de leitura estão em `/api/v1/`:

- `GET /api/v1/health/`;
- `GET /api/v1/me/`;
- `GET /api/v1/account/`;
- `GET /api/v1/movements/`.

Elas usam a sessão Django nesta fase. Antes de um aplicativo distribuído, deve-se introduzir OAuth 2.1/OpenID Connect com PKCE, rotação de refresh tokens, registro seguro do dispositivo e atestado de integridade quando disponível.

## Caminho recomendado

1. validar a PWA com usuários idosos;
2. documentar a API com OpenAPI;
3. extrair componentes e tokens para um pacote de design compartilhado;
4. criar o cliente Flutter, React Native ou nativo;
5. manter ledger e regras financeiras exclusivamente no servidor;
6. adicionar notificações push somente com consentimento granular.

Nunca armazene saldo, chave Pix, comprovantes ou tokens sensíveis em cache web, `localStorage` ou banco local sem um modelo de ameaça e criptografia apropriados.
