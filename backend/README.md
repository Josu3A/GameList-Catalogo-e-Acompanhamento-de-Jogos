# GameList — Backend (Django + DRF)

API REST do GameList com Django 5.2 LTS, Django REST Framework e PostgreSQL. O **Django Admin**
(`/admin/`) é o painel do administrador para o CRUD do catálogo.

> A forma mais simples de subir tudo é com **Docker** — veja o [README da raiz](../README.md).
> As instruções abaixo são para rodar o backend direto na máquina.

## Setup

Pré-requisitos: Python 3.11+ e PostgreSQL (instância local na porta **5433** — ver LOG.md).

```powershell
cd backend
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

# configuração de ambiente
copy .env.example .env    # e preencha DB_PASSWORD (e demais valores se necessário)
# Steam (opcional): STEAM_API_KEY + FRONTEND_URL habilitam sync de biblioteca/conquistas.

# criar o banco (uma vez)
psql -h localhost -p 5433 -U postgres -c "CREATE DATABASE gamelist;"

# estrutura + seed (3 usuários demo + os 100 jogos famosos da Steam, offline)
.venv\Scripts\python manage.py migrate
.venv\Scripts\python manage.py seed_demo

# rodar
.venv\Scripts\python manage.py runserver
```

Testes: `.venv\Scripts\python manage.py test`

## Usuários de demonstração (senha `senha123`)

| E-mail | Papel |
|---|---|
| admin@gamelist.dev | admin |
| ana@gamelist.dev | comum |
| bruno@gamelist.dev | comum |

## Endpoints

Autenticação por **sessão + cookies**. Para POST/PATCH/DELETE, obtenha o cookie `csrftoken`
em `GET /api/auth/csrf/` e envie o header `X-CSRFToken`.

| Rota | Métodos | Acesso |
|---|---|---|
| `/api/auth/register/` | POST | público — cria usuário **comum** |
| `/api/auth/login/` · `/api/auth/logout/` | POST | público · autenticado |
| `/api/auth/me/` | GET / PATCH | autenticado |
| `/api/auth/steam/login/` · `/api/auth/steam/callback/` | GET | login/vínculo via Steam (OpenID) |
| `/api/auth/steam/disconnect/` | POST | autenticado — desvincula a Steam |
| `/api/games/` | GET / POST / PATCH / DELETE | leitura pública (só `publicado` p/ não-admin); escrita **só admin** |
| `/api/games/steam-preview/` | POST | **só admin** — autofill da loja Steam (não cria o jogo) |
| `/api/genres/` `/api/platforms/` `/api/developers/` `/api/publishers/` | GET / escrita | leitura pública; escrita só admin |
| `/api/my-games/` | CRUD | autenticado — **sempre a própria lista** |
| `/api/my-games/steam-sync/` | POST | autenticado — importa jogos + horas da Steam |
| `/api/my-games/steam-achievements/` | POST | autenticado — sincroniza conquistas de um jogo |
| `/api/profiles/<user_id>/` | GET | público (404 se o perfil for privado) |
| `/admin/` | — | painel do administrador (Django Admin) |

Filtros úteis: `/api/games/?search=hades`, `?genero=<id>`, `?plataforma=<id>`, `?ano=2022`;
`/api/my-games/?status=jogando`, `?platinado=true`.

## Catálogo (100 jogos da Steam)

O catálogo vem de um **snapshot versionado** (`catalog/data/steam_top_games.json`) lido pelo app
`catalog` — nada a configurar. Já entra no `seed_demo`; comandos idempotentes (casam por
`steam_appid`):

```powershell
.venv\Scripts\python manage.py seed_steam_top --offline   # só o catálogo, do snapshot, sem rede
.venv\Scripts\python manage.py seed_steam_top             # (online) busca/atualiza pela Steam
.venv\Scripts\python manage.py seed_steam_top --update    # atualiza os existentes e refaz o snapshot
```

## Estrutura

- `config/` — settings (lê `.env`), rotas raiz
- `accounts/` — modelo `User` customizado (tabela `users`), auth por sessão, permissões de papel
- `catalog/` — `Game` + taxonomias (gêneros, plataformas, devs, publishers), `Achievement`,
  `seed_steam_top` + snapshot dos 100 jogos, integração Steam (autofill)
- `library/` — `UserGame` (lista pessoal), perfil público, comando `seed_demo`, sync Steam
- `social/` — amigos, reviews/curtidas, listas customizadas e notificações

Esquema de referência em `../ESQUEMA_DADOS.md` e `../db/schema.sql`; a fonte da verdade do schema
são as **migrações Django**.
