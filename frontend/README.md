# GameCheck — Frontend (React + Vite + TypeScript)

SPA que consome a API DRF do backend ([../backend/](../backend/)). Tema escuro com **Mantine**,
estado de servidor com **TanStack Query**, roteamento com **react-router**.

> A forma mais simples de subir tudo é com **Docker** — veja o [README da raiz](../README.md).
> As instruções abaixo são para rodar o frontend direto na máquina.

## Como rodar

Pré-requisitos: **Node 18+** e npm, com o **backend rodando** em `http://localhost:8000`
(ver [../backend/README.md](../backend/README.md)).

```bash
npm install
npm run dev        # http://localhost:5173
```

Variável de ambiente (arquivo `.env`, já incluído):

```
VITE_API_BASE_URL=http://localhost:8000
```

A origem `http://localhost:5173` já está liberada no CORS/CSRF do backend. Autenticação é por
**sessão + cookie**: o cliente busca o cookie CSRF (`GET /api/auth/csrf/`) e envia `X-CSRFToken`
nas mutações (ver [src/api/client.ts](src/api/client.ts)).

Usuários de demonstração (senha `senha123`): `admin@gamelist.dev` (admin), `ana@gamelist.dev`,
`bruno@gamelist.dev`.

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
  theme.ts     tema Mantine (escuro, paleta violeta→azul da logo)
  App.tsx      rotas
  main.tsx     providers (Mantine + QueryClient + Router + Auth)
```

Mapa completo das telas em [../FRONTEND_TELAS.md](../FRONTEND_TELAS.md).
