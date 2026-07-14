# GameList — Backend (Django + DRF)

API REST do GameList com Django 5.2 LTS, Django REST Framework e PostgreSQL.
O **Django Admin** (`/admin/`) é o painel do administrador para o CRUD do catálogo.

## Setup

Pré-requisitos: Python 3.11+ e PostgreSQL (instância local na porta **5433** — ver LOG.md).

```powershell
cd backend
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

# configuração de ambiente
copy .env.example .env    # e preencha DB_PASSWORD (e demais valores se necessário)
# Para a integração Steam: preencha STEAM_API_KEY (https://steamcommunity.com/dev/apikey)
# e FRONTEND_URL. Login OpenID e autofill da loja funcionam sem a chave; sync de
# biblioteca/conquistas e nome/avatar do perfil exigem a chave.

# criar o banco (uma vez)
psql -h localhost -p 5433 -U postgres -c "CREATE DATABASE gamelist;"

# estrutura + seed (3 usuários demo + catálogo dos 100 jogos famosos da Steam)
.venv\Scripts\python manage.py migrate
.venv\Scripts\python manage.py seed_demo

# rodar
.venv\Scripts\python manage.py runserver
```

Testes: `.venv\Scripts\python manage.py test`

## Carregar o catálogo (100 jogos famosos da Steam)

Não há nada a configurar em `settings.py`: o catálogo vem de um **snapshot versionado**
(`catalog/data/steam_top_games.json`) lido direto pelo app `catalog`. "Carregar" é só rodar
um comando — todos são **idempotentes** (casam por `steam_appid`, podem rodar de novo):

```powershell
# forma padrão: já embutido no seed (usuários demo + os 100 jogos, offline, sem rede)
.venv\Scripts\python manage.py seed_demo

# só o catálogo (sem os usuários/listas de demonstração), do snapshot offline
.venv\Scripts\python manage.py seed_steam_top --offline

# opcional: buscar/atualizar os 100 direto da Steam (online, ~2 min) e refazer o snapshot
.venv\Scripts\python manage.py seed_steam_top            # cria/pula
.venv\Scripts\python manage.py seed_steam_top --update   # atualiza os existentes
```

Ou seja, num ambiente novo o catálogo entra sozinho no passo `seed_demo` do Setup acima.

## Usuários de demonstração (seed_demo)

| E-mail | Papel | Senha |
|---|---|---|
| admin@gamelist.dev | admin | senha123 |
| ana@gamelist.dev | comum | senha123 |
| bruno@gamelist.dev | comum | senha123 |

## Endpoints

Autenticação por **sessão + cookies**. Para POST/PATCH/DELETE, obtenha o cookie
`csrftoken` em `GET /api/auth/csrf/` e envie o header `X-CSRFToken`.

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

Filtros úteis: `/api/games/?search=hades`, `?genero=<id>`, `?plataforma=<id>`,
`?ano=2022`; `/api/my-games/?status=jogando`, `?platinado=true`.

## Estrutura

- `config/` — settings (lê `.env`), rotas raiz
- `accounts/` — modelo `User` customizado (tabela `users`), auth por sessão, permissões de papel
- `catalog/` — `Game` + taxonomias normalizadas (gêneros, plataformas, devs, publishers) e
  `Achievement`; comando `seed_steam_top` + snapshot `data/steam_top_games.json` (100 jogos)
- `library/` — `UserGame` (lista pessoal), perfil público, comando `seed_demo`
- `social/` — modelos das extensões futuras (amizades, curtidas, listas, notificações) — **sem endpoints**

O esquema de referência continua documentado em `../ESQUEMA_DADOS.md` e
`../db/schema.sql`; a fonte da verdade do schema agora são as **migrações Django**
(divergências pontuais documentadas no LOG.md da raiz).
