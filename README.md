# GameCheck

Aplicação web de **catálogo e acompanhamento de jogos**, no estilo MyAnimeList/Letterboxd,
com características de rede social. A plataforma mantém um **catálogo central de jogos** curado
por administradores; o usuário comum navega esse catálogo e monta sua **lista pessoal**
(jogando, completo, quero jogar, pausado, abandonado, platinado), com nota, horas jogadas e
datas. Perfil público destaca as **platinas**, e há amigos, reviews com curtidas, listas
customizadas e **integração com a Steam** (login, autofill do catálogo e sync de biblioteca e conquistas).

Projeto da disciplina Tópicos Avançados em Ciência da Computação XI — Atividade CRUD com banco relacional,
entidade de usuário e **dois papéis** (comum × admin) com acessos distintos.

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Django 5.2 LTS + Django REST Framework |
| Frontend | React 18 + Vite + TypeScript |
| Banco | PostgreSQL 16 |
| Infra | Docker (3 serviços) |

## Rodar com Docker (recomendado)

Sobe os três serviços em containers: **PostgreSQL**, **backend** (Django + DRF) e **frontend**
(SPA React/Vite servido por nginx). É o caminho mais simples — não exige Python, Node nem
Postgres instalados na máquina, só o Docker.

**Pré-requisito:** Docker + Docker Compose (Docker Desktop no Windows/Mac).

Na pasta `GameCheck/`:

```bash
docker compose up --build
```

Na primeira vez o backend espera o Postgres ficar pronto, aplica as *migrations* e roda
`python manage.py seed_demo` (idempotente): 3 usuários demo + **~100 jogos famosos da Steam**
(carregados do snapshot offline `backend/catalog/data/steam_top_games.json`, **sem acessar a
rede**) + listas e rede social. Como o seed é idempotente, roda a cada start sem duplicar.

| Serviço  | URL |
|----------|-----|
| Frontend | http://localhost:3000 |
| Backend (API) | http://localhost:8000 |
| Django Admin | http://localhost:8000/admin/ |
| Postgres | localhost:**5434** (host) → 5432 (container) |

### Logins de demonstração

| E-mail | Senha | Papel |
|---|---|---|
| admin@gamelist.dev | senha123 | admin (acessa o `/admin/`) |
| ana@gamelist.dev | senha123 | comum (tem platina + reviews) |
| bruno@gamelist.dev | senha123 | comum |

### Configuração opcional

Os defaults do [docker-compose.yml](docker-compose.yml) já deixam o stack funcional. Para
sobrescrever segredos/integrações, crie um arquivo `.env` **na pasta `GameCheck`**:

```env
SECRET_KEY=uma-chave-secreta-de-verdade
DB_PASSWORD=uma-senha-forte
STEAM_API_KEY=...   # habilita sync de biblioteca/conquistas Steam
RAWG_API_KEY=...    # habilita o carrossel de "Próximos Lançamentos"
```

### Comandos úteis

```bash
docker compose up --build -d      # sobe em background
docker compose logs -f backend    # acompanha os logs do backend
docker compose exec backend python manage.py createsuperuser
docker compose down               # para os containers (mantém os dados)
docker compose down -v            # para e APAGA os volumes (banco + uploads)
```

### Como o banco é criado

O schema vem das **migrations do Django** (fonte da verdade), não do `db/schema.sql`. Nos
containers, os dados entram via `seed_demo` (app `library`), que usa o ORM — gera senhas
válidas (os logins funcionam) e carrega os ~100 jogos do snapshot offline. O `db/schema.sql`/
`db/seed.sql` seguem apenas como documentação/entrega SQL.

## Rodar sem Docker

Para desenvolvimento local com os serviços rodando direto na máquina, veja as instruções de
cada parte:

- **Backend** (Python 3.11+ e PostgreSQL): [backend/README.md](backend/README.md)
- **Frontend** (Node 18+ e npm): [frontend/README.md](frontend/README.md)

## Estrutura do repositório

```
GameCheck/
  backend/     API Django + DRF (accounts, catalog, library, social) e Dockerfile
  frontend/    SPA React + Vite + TypeScript e Dockerfile
  db/          schema.sql e seed.sql (documentação/entrega SQL do banco)
  docker-compose.yml   orquestra db + backend + frontend
```

## Documentação do projeto

- [CONTEXTO_PROJETO.md](CONTEXTO_PROJETO.md) — ideia, requisitos e decisões da atividade
- [ESQUEMA_DADOS.md](ESQUEMA_DADOS.md) / [GameCheck.dbml](GameCheck.dbml) — modelagem do banco
- [FRONTEND_TELAS.md](FRONTEND_TELAS.md) — mapa das telas do frontend
- [DOCKER.md](DOCKER.md) — detalhes da execução com Docker
- [LOG.md](LOG.md) — log cronológico de desenvolvimento
