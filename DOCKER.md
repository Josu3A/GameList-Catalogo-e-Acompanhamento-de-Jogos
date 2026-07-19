# GameCheck — Execução com Docker

Sobe os três serviços do projeto em containers: **PostgreSQL**, **backend**
(Django + DRF) e **frontend** (SPA React/Vite servido por nginx).

## Pré-requisitos

- Docker + Docker Compose (Docker Desktop no Windows/Mac).

## Subir tudo

Na pasta `GameCheck/`:

```bash
docker compose up --build
```

Na primeira vez o backend espera o Postgres ficar pronto, aplica as *migrations*
e popula os dados de demonstração (`python manage.py seed_demo`, idempotente):
3 usuários + **~100 jogos famosos da Steam** (carregados do snapshot offline
`catalog/data/steam_top_games.json`, sem acessar a rede) + listas e rede social.

| Serviço  | URL                          |
|----------|------------------------------|
| Frontend | http://localhost:3000        |
| Backend  | http://localhost:8000        |
| Admin    | http://localhost:8000/admin/ |
| Postgres | localhost:5434 (host) → 5432 (container) |

## Logins de demonstração

Todos com a senha **`senha123`**:

| E-mail               | Papel |
|----------------------|-------|
| admin@gamelist.dev   | admin (acessa o `/admin/`) |
| ana@gamelist.dev     | comum |
| bruno@gamelist.dev   | comum |

## Configuração opcional

Os defaults do `docker-compose.yml` já deixam o stack funcional. Para
sobrescrever segredos/integrações, crie um arquivo `.env` **nesta pasta**:

```env
SECRET_KEY=uma-chave-secreta-de-verdade
DB_PASSWORD=uma-senha-forte
STEAM_API_KEY=...   # habilita sync de biblioteca/conquistas Steam
RAWG_API_KEY=...    # habilita o carrossel de "Próximos Lançamentos"
```

> A URL do backend usada pelo frontend é embutida no build (Vite). O padrão
> aponta para `http://localhost:8000`. Para trocar, ajuste o build arg
> `VITE_API_BASE_URL` do serviço `frontend` no `docker-compose.yml`.

## Comandos úteis

```bash
docker compose up --build -d      # sobe em background
docker compose logs -f backend    # acompanha os logs do backend
docker compose exec backend python manage.py createsuperuser
docker compose down               # para os containers (mantém os dados)
docker compose down -v            # para e APAGA os volumes (banco + uploads)
```

## Como o banco é criado

O schema vem das **migrations do Django** (fonte da verdade), não do
`db/schema.sql`. O `db/seed.sql` continua servindo para carga manual; nos
containers, os dados entram via o comando `seed_demo` (app `library`) — ele usa
o ORM (gera senhas válidas, faz os logins funcionarem) e carrega os ~100 jogos
do snapshot offline `catalog/data/steam_top_games.json`. É idempotente, então
roda a cada start sem duplicar.
