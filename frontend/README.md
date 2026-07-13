# GameList — Frontend (React + Vite + TypeScript)

SPA que consome a API DRF do backend ([../backend/](../backend/)). Tema escuro com
**Mantine**, estado de servidor com **TanStack Query**, roteamento com **react-router**.

## Pré-requisitos

- Node 18+ (testado com Node 24) e npm.
- O **backend rodando** em `http://localhost:8000` (`python manage.py runserver`),
  apontando para o PostgreSQL do projeto (porta 5433) já populado com `seed_demo`.

## Como rodar

```bash
npm install
npm run dev        # http://localhost:5173
```

Variável de ambiente (arquivo `.env`, já incluído):

```
VITE_API_BASE_URL=http://localhost:8000
```

A origem `http://localhost:5173` já está liberada no `CORS_ALLOWED_ORIGINS`/
`CSRF_TRUSTED_ORIGINS` do backend. Autenticação é por **sessão + cookie**; o cliente
busca o cookie CSRF (`GET /api/auth/csrf/`) e envia `X-CSRFToken` nas mutações
(ver [src/api/client.ts](src/api/client.ts)).

### Usuários de demonstração (senha `senha123`)

| E-mail | Papel |
|---|---|
| `admin@gamelist.dev` | admin (vê `/admin/*`) |
| `ana@gamelist.dev` | comum (tem platina + reviews) |
| `bruno@gamelist.dev` | comum |

## Scripts

- `npm run dev` — servidor de desenvolvimento (Vite).
- `npm run build` — typecheck (`tsc --noEmit`) + build de produção.
- `npm run typecheck` — só a checagem de tipos.
- `npm run preview` — serve o build de produção.

## Estrutura

```
src/
  api/         client.ts (axios + CSRF) e um módulo por recurso (auth, games, library, profiles, social)
  auth/        AuthContext (sessão) + guards (RequireAuth, RequireAdmin)
  components/  Layout, Navbar, GameCard, StatusBadge, ReviewCard, UserGameFormModal
  lib/         labels.ts (rótulos de status, textos de notificação, datas)
  pages/       auth/ catalog/ library/ profile/ admin/ social/
  types/       interfaces TS espelhando os serializers do backend
  theme.ts     tema Mantine (escuro; cores/tipografia a definir)
  App.tsx      rotas
  main.tsx     providers (Mantine + QueryClient + Router + Auth)
```

## Telas

MVP: catálogo (busca/filtros/paginação), detalhe do jogo, lista pessoal, perfil público
(com platinas), editar perfil, login/registro. Admin (React): CRUD de jogos (trata **409**
ao excluir jogo em listas) e das taxonomias. Social: amigos, notificações (com badge),
listas customizadas e reviews com curtir. Mapa completo em
[../FRONTEND_TELAS.md](../FRONTEND_TELAS.md).

## Notas

- Troca de e-mail/senha (`/settings/account`) não tem endpoint dedicado — fica no Django
  Admin por enquanto.
- O bundle de produção é único (~660 kB) — aceitável para o escopo acadêmico; dá para
  aplicar code-splitting por rota depois, se necessário.
