# Esquema de Dados — GameList

> Modelo relacional da aplicação. Projetado para ser **normalizado** e **aberto a
> extensões** (notadamente a integração com a Steam), mantendo o MVP obrigatório
> 100% funcional de forma independente.

## Visão geral

O modelo se organiza em quatro grupos:

1. **Núcleo (MVP)** — `users`, `games`, `user_games`.
2. **Catálogo normalizado** — `genres`, `platforms`, `developers`, `publishers` + tabelas
   de junção (um jogo tem vários gêneros/plataformas/desenvolvedoras/publicadoras).
3. **Integração Steam (extensão futura)** — campos `steam_id`/`steam_appid` e as
   tabelas `achievements` e `user_achievements`.
4. **Rede social e organização** — `friendships`, `review_likes`, `lists`/`list_items`
   e `notifications` (a review em si é coluna de `user_games`).

### Convenções gerais

- **PK**: toda tabela tem `id BIGSERIAL PRIMARY KEY` (chave surrogate).
- **Timestamps**: entidades principais têm `created_at` e `updated_at`
  (`TIMESTAMPTZ NOT NULL DEFAULT now()`).
- **Enums**: modelados como `VARCHAR` + `CHECK` (mais fáceis de estender que o
  `ENUM` nativo do Postgres, que exige `ALTER TYPE` em migração dedicada).
- **Campos Steam**: sempre `nullable` — a conexão com a Steam é opcional e não pode
  bloquear o cadastro manual.

---

## 1. Núcleo (MVP)

### 1.1 `users`

| Campo | Tipo | Restrições |
|---|---|---|
| id | BIGSERIAL | PK |
| nome | VARCHAR(100) | `NOT NULL` |
| email | VARCHAR(255) | `UNIQUE NOT NULL` |
| senha_hash | VARCHAR(255) | `NOT NULL` — nunca senha em texto puro |
| tipo_usuario | VARCHAR(20) | `NOT NULL CHECK (tipo_usuario IN ('comum','admin'))` |
| bio | TEXT | nullable |
| avatar_url | VARCHAR(500) | nullable — **caminho** do avatar enviado por upload (ex.: `avatars/<uuid>.jpg`), servido como mídia; ver nota abaixo |
| perfil_publico | BOOLEAN | `NOT NULL DEFAULT true` |
| steam_id | VARCHAR(20) | nullable, `UNIQUE` — SteamID64 (extensão futura) |
| created_at | TIMESTAMPTZ | `NOT NULL DEFAULT now()` |
| updated_at | TIMESTAMPTZ | `NOT NULL DEFAULT now()` |

> **`avatar_url` — upload (não URL externa):** o avatar é enviado por **upload** na
> edição de perfil. O backend guarda o **caminho relativo** do arquivo nesta coluna
> (ex.: `avatars/<uuid>.jpg`) e a API o serializa como **URL de mídia** — o usuário vê a
> foto, nunca o caminho. No Django é um `ImageField` (mesma coluna `VARCHAR(500)`, sem
> mudança de DDL). Limites do upload: JPG/PNG/WEBP/GIF, até 2 MB. Ao vincular a Steam, o
> avatar do perfil Steam é **baixado** e salvo também como mídia local (ver LOG.md 2026-07-13).

### 1.2 `games`

Catálogo central. CRUD completo restrito ao admin; leitura pública.

| Campo | Tipo | Restrições |
|---|---|---|
| id | BIGSERIAL | PK |
| titulo | VARCHAR(200) | `NOT NULL` |
| capa_url | VARCHAR(500) | nullable |
| banner_url | VARCHAR(500) | nullable — `header_image` da Steam |
| ano_lancamento | INTEGER | nullable |
| sinopse | TEXT | nullable |
| status_publicacao | VARCHAR(20) | `NOT NULL DEFAULT 'rascunho' CHECK (status_publicacao IN ('rascunho','publicado'))` |
| steam_appid | INTEGER | nullable, `UNIQUE` — chave de casamento com a Steam |
| created_at | TIMESTAMPTZ | `NOT NULL DEFAULT now()` |
| updated_at | TIMESTAMPTZ | `NOT NULL DEFAULT now()` |

> `status_publicacao` suporta o fluxo de autopreenchimento via Steam: o admin cadastra
> como `rascunho`, o job preenche os campos, o admin revisa e muda para `publicado`.
> Gênero, plataforma e desenvolvedora **não** ficam aqui — foram normalizados (ver §2).

### 1.3 `user_games`

A "lista pessoal": relação N:N entre `users` e `games`.

| Campo | Tipo | Restrições |
|---|---|---|
| id | BIGSERIAL | PK |
| user_id | BIGINT | FK → `users(id)` `NOT NULL ON DELETE CASCADE` |
| game_id | BIGINT | FK → `games(id)` `NOT NULL ON DELETE RESTRICT` |
| status | VARCHAR(20) | `NOT NULL CHECK (status IN ('jogando','completo','quero_jogar','pausado','abandonado'))` |
| nota | DECIMAL(3,1) | nullable, `CHECK (nota >= 0 AND nota <= 10)` |
| horas_jogadas | DECIMAL(7,1) | `NOT NULL DEFAULT 0 CHECK (horas_jogadas >= 0)` |
| platinado | BOOLEAN | `NOT NULL DEFAULT false` |
| data_inicio | DATE | nullable |
| data_fim | DATE | nullable |
| review | TEXT | nullable — texto opcional da review do usuário sobre o jogo |
| fonte | VARCHAR(20) | `NOT NULL DEFAULT 'manual' CHECK (fonte IN ('manual','steam_sync'))` |
| created_at | TIMESTAMPTZ | `NOT NULL DEFAULT now()` |
| updated_at | TIMESTAMPTZ | `NOT NULL DEFAULT now()` |

**Restrições:**
- `UNIQUE (user_id, game_id)` — um jogo não se repete na lista de um usuário.
- `status` e `platinado` são **independentes**: um jogo pode estar `completo` **e**
  `platinado = true`. O destaque de platinas no perfil busca `platinado = true`.
- `fonte` distingue o que foi preenchido manualmente do que veio da sincronização Steam.
- `review` fica **aqui** (e não em tabela própria) porque uma review é a opinião de *um
  usuário sobre um jogo* — exatamente a chave desta linha. Depende funcionalmente da PK
  de `user_games`, então permanece normalizado; uma tabela `reviews` separada duplicaria
  a relação usuário↔jogo já existente aqui. As **curtidas** da review, por serem N:N,
  vão para a tabela `review_likes` (ver §4.2).

---

## 2. Catálogo normalizado

Um jogo tem vários gêneros, plataformas e desenvolvedoras — e a Storefront API da Steam
retorna esses campos como listas. Por isso são tabelas próprias, ligadas por junção N:N.

### 2.1 Tabelas de referência

**`genres`**

| Campo | Tipo | Restrições |
|---|---|---|
| id | BIGSERIAL | PK |
| nome | VARCHAR(100) | `UNIQUE NOT NULL` |

**`platforms`**

| Campo | Tipo | Restrições |
|---|---|---|
| id | BIGSERIAL | PK |
| nome | VARCHAR(100) | `UNIQUE NOT NULL` |

**`developers`**

| Campo | Tipo | Restrições |
|---|---|---|
| id | BIGSERIAL | PK |
| nome | VARCHAR(150) | `UNIQUE NOT NULL` |

**`publishers`**

| Campo | Tipo | Restrições |
|---|---|---|
| id | BIGSERIAL | PK |
| nome | VARCHAR(150) | `UNIQUE NOT NULL` |

> Separada de `developers` porque a Storefront API da Steam retorna `developers` e
> `publishers` como campos distintos, e a mesma empresa pode ser dev de um jogo e
> publisher de outro.

### 2.2 Tabelas de junção

**`game_genres`**

| Campo | Tipo | Restrições |
|---|---|---|
| game_id | BIGINT | FK → `games(id)` `ON DELETE CASCADE` |
| genre_id | BIGINT | FK → `genres(id)` `ON DELETE CASCADE` |
| | | PK composta `(game_id, genre_id)` |

**`game_platforms`**

| Campo | Tipo | Restrições |
|---|---|---|
| game_id | BIGINT | FK → `games(id)` `ON DELETE CASCADE` |
| platform_id | BIGINT | FK → `platforms(id)` `ON DELETE CASCADE` |
| | | PK composta `(game_id, platform_id)` |

**`game_developers`**

| Campo | Tipo | Restrições |
|---|---|---|
| game_id | BIGINT | FK → `games(id)` `ON DELETE CASCADE` |
| developer_id | BIGINT | FK → `developers(id)` `ON DELETE CASCADE` |
| | | PK composta `(game_id, developer_id)` |

**`game_publishers`**

| Campo | Tipo | Restrições |
|---|---|---|
| game_id | BIGINT | FK → `games(id)` `ON DELETE CASCADE` |
| publisher_id | BIGINT | FK → `publishers(id)` `ON DELETE CASCADE` |
| | | PK composta `(game_id, publisher_id)` |

> **Simplificação opcional para o MVP:** se preferir não normalizar já de início, é
> possível manter `genero`/`plataforma`/`desenvolvedora` como `VARCHAR` direto em `games`
> e migrar para estas tabelas depois. A versão normalizada é a recomendada por deixar o
> banco robusto e pronto para a Steam.

---

## 3. Integração Steam (extensão futura)

Apoia-se nos campos `users.steam_id` e `games.steam_appid` (§1) mais as duas tabelas
abaixo, que modelam conquistas. Tudo opcional — não afeta o MVP.

### 3.1 `achievements`

Esquema de conquistas de um jogo (populado via `GetSchemaForGame`).

| Campo | Tipo | Restrições |
|---|---|---|
| id | BIGSERIAL | PK |
| game_id | BIGINT | FK → `games(id)` `NOT NULL ON DELETE CASCADE` |
| steam_apiname | VARCHAR(200) | `NOT NULL` — nome interno da conquista na Steam |
| nome | VARCHAR(200) | `NOT NULL` |
| descricao | TEXT | nullable |
| icon_url | VARCHAR(500) | nullable |
| | | `UNIQUE (game_id, steam_apiname)` |

### 3.2 `user_achievements`

Conquistas desbloqueadas por um usuário (via `GetPlayerAchievements`).

| Campo | Tipo | Restrições |
|---|---|---|
| id | BIGSERIAL | PK |
| user_id | BIGINT | FK → `users(id)` `NOT NULL ON DELETE CASCADE` |
| achievement_id | BIGINT | FK → `achievements(id)` `NOT NULL ON DELETE CASCADE` |
| desbloqueada_em | TIMESTAMPTZ | nullable |
| | | `UNIQUE (user_id, achievement_id)` |

> O percentual de conclusão (para sugerir marcar como `platinado`) é derivado por
> contagem: `user_achievements` do usuário para o jogo ÷ total de `achievements` do jogo.

---

## 4. Rede social e organização

`friendships` segue como extensão futura; `review_likes`, `lists`/`list_items` e
`notifications` foram incorporadas ao esquema.

### 4.1 `friendships` (extensão futura)

| Campo | Tipo | Restrições |
|---|---|---|
| id | BIGSERIAL | PK |
| user_id | BIGINT | FK → `users(id)` `NOT NULL ON DELETE CASCADE` — quem solicitou |
| friend_id | BIGINT | FK → `users(id)` `NOT NULL ON DELETE CASCADE` — quem recebeu |
| status | VARCHAR(20) | `NOT NULL CHECK (status IN ('pendente','aceito'))` |
| created_at | TIMESTAMPTZ | `NOT NULL DEFAULT now()` |

**Restrições:**
- `UNIQUE (user_id, friend_id)` — não duplica a mesma solicitação.
- `CHECK (user_id <> friend_id)` — ninguém é amigo de si mesmo.

### 4.2 `review_likes`

Curtidas em reviews. A "review" é a linha de `user_games` cujo campo `review` está
preenchido — logo, o like referencia `user_games(id)`.

| Campo | Tipo | Restrições |
|---|---|---|
| user_game_id | BIGINT | FK → `user_games(id)` `NOT NULL ON DELETE CASCADE` — a review curtida |
| user_id | BIGINT | FK → `users(id)` `NOT NULL ON DELETE CASCADE` — quem curtiu |
| created_at | TIMESTAMPTZ | `NOT NULL DEFAULT now()` |
| | | PK composta `(user_game_id, user_id)` |

**Restrições:**
- PK composta `(user_game_id, user_id)` impede curtir a mesma review duas vezes.
- Relação N:N (vários usuários curtem várias reviews) — por isso é tabela própria, e não
  coluna. Contagem de likes = `COUNT(*)` em `review_likes` por `user_game_id`.

### 4.3 `lists` e `list_items`

Listas/coleções customizadas do usuário (ex.: "Top 10 RPGs"), independentes do `status`
da lista pessoal.

**`lists`**

| Campo | Tipo | Restrições |
|---|---|---|
| id | BIGSERIAL | PK |
| user_id | BIGINT | FK → `users(id)` `NOT NULL ON DELETE CASCADE` |
| nome | VARCHAR(150) | `NOT NULL` |
| descricao | TEXT | nullable |
| publica | BOOLEAN | `NOT NULL DEFAULT true` |
| created_at | TIMESTAMPTZ | `NOT NULL DEFAULT now()` |
| updated_at | TIMESTAMPTZ | `NOT NULL DEFAULT now()` |
| | | `UNIQUE (user_id, nome)` — o usuário não repete o nome de lista |

**`list_items`** — jogos dentro de uma lista (N:N entre `lists` e `games`).

| Campo | Tipo | Restrições |
|---|---|---|
| list_id | BIGINT | FK → `lists(id)` `NOT NULL ON DELETE CASCADE` |
| game_id | BIGINT | FK → `games(id)` `NOT NULL ON DELETE RESTRICT` |
| ordem | INTEGER | nullable — posição opcional na lista |
| added_at | TIMESTAMPTZ | `NOT NULL DEFAULT now()` |
| | | PK composta `(list_id, game_id)` — jogo não se repete na mesma lista |

### 4.4 `notifications`

Notificações do usuário (pedido de amizade recebido/aceito, curtida em review).

| Campo | Tipo | Restrições |
|---|---|---|
| id | BIGSERIAL | PK |
| user_id | BIGINT | FK → `users(id)` `NOT NULL ON DELETE CASCADE` — destinatário |
| actor_id | BIGINT | FK → `users(id)` nullable `ON DELETE SET NULL` — quem gerou o evento |
| tipo | VARCHAR(20) | `NOT NULL CHECK (tipo IN ('pedido_amizade','amizade_aceita','review_curtida'))` |
| friendship_id | BIGINT | FK → `friendships(id)` nullable `ON DELETE CASCADE` — preenchido em `pedido_amizade`/`amizade_aceita` |
| user_game_id | BIGINT | FK → `user_games(id)` nullable `ON DELETE CASCADE` — preenchido em `review_curtida` |
| lida | BOOLEAN | `NOT NULL DEFAULT false` |
| created_at | TIMESTAMPTZ | `NOT NULL DEFAULT now()` |

**Restrições:**
- `CHECK` de referência exatamente-uma, conforme o `tipo`:
  ```sql
  CHECK (
    (tipo IN ('pedido_amizade','amizade_aceita')
       AND friendship_id IS NOT NULL AND user_game_id IS NULL)
    OR
    (tipo = 'review_curtida'
       AND user_game_id IS NOT NULL AND friendship_id IS NULL)
  )
  ```
- Integridade referencial real via FKs separadas (opção 100% normalizada escolhida sobre a
  alternativa de um `referencia_id` polimórfico sem FK). Novos tipos de notificação exigem
  uma nova coluna FK e a atualização deste `CHECK`.

---

## 5. Índices recomendados

Além dos criados automaticamente por PK e `UNIQUE`:

- `user_games (user_id)` — montar a lista/perfil de um usuário.
- `user_games (game_id)` — quem tem determinado jogo na lista.
- `user_games (user_id) WHERE platinado = true` — destaque de platinas no perfil (índice parcial).
- `games (steam_appid)` — casamento na sincronização (já coberto pelo `UNIQUE`).
- `friendships (friend_id)` — solicitações recebidas por um usuário.
- `review_likes (user_id)` — reviews que um usuário curtiu.
- `notifications (user_id, lida)` — notificações não lidas de um usuário.

---

## 6. Resumo das decisões de modelagem

| Decisão | Escolha | Por quê |
|---|---|---|
| `status` vs `platinado` | flags independentes | permite jogo `completo` **e** `platinado`; destaque busca `platinado = true` |
| `ON DELETE` de `user_games.game_id` | `RESTRICT` | impede apagar do catálogo um jogo ainda presente em listas (preserva histórico) |
| `ON DELETE` de FKs de usuário | `CASCADE` | apagar um usuário limpa lista/conquistas/amizades dele |
| Enums | `VARCHAR` + `CHECK` | mais fácil estender que `ENUM` nativo |
| gênero/plataforma/dev | tabelas normalizadas N:N | um jogo tem vários; alinha com as listas da Steam |
| campos Steam | nullable, opcionais | MVP funciona sem Steam; integração não bloqueia cadastro manual |
| `status_publicacao` em `games` | `rascunho`/`publicado` | suporta revisão do admin no autopreenchimento |
| review | coluna em `user_games` | opinião de 1 usuário sobre 1 jogo depende da PK da linha; evita duplicar a relação usuário↔jogo |
| curtidas de review | tabela `review_likes` (N:N) | vários usuários curtem várias reviews; não cabe em coluna |
| developer vs publisher | tabelas separadas | Steam retorna os dois campos; mesma empresa pode ter papéis diferentes por jogo |
| referência da notificação | FKs separadas (`friendship_id`, `user_game_id`) + `CHECK` | integridade referencial real e 100% normalizada; `CHECK` garante exatamente uma referência por `tipo` (ver §4.4) |

---

## 7. Diagrama Entidade-Relacionamento (DER)

```
        GENRES          PLATFORMS         DEVELOPERS
          |                 |                  |
          | N:N             | N:N              | N:N
     game_genres      game_platforms    game_developers
          |                 |                  |
          +--------+--------+---------+--------+
                   |                  |
                   v                  v
                +------------------------------+
                |            GAMES             |
                | id (PK)                      |
                | titulo                       |
                | capa_url / banner_url        |
                | ano_lancamento / sinopse     |
                | status_publicacao            |
                | steam_appid (UNIQUE, null)   |
                +------------------------------+
                   | 1                    | 1
                   |                      |
                   | N                    | N
        +----------------------+   +------------------+
        |     USER_GAMES       |   |   ACHIEVEMENTS   |
        | id (PK)              |   | id (PK)          |
        | user_id  (FK)       |   | game_id (FK)     |
        | game_id  (FK)       |   | steam_apiname    |
        | status / nota       |   | nome / icon_url  |
        | horas_jogadas       |   +------------------+
        | platinado           |            | 1
        | data_inicio/fim     |            |
        | fonte               |            | N
        | UNIQUE(user,game)   |   +----------------------+
        +----------------------+   |  USER_ACHIEVEMENTS   |
                   | N             | id (PK)              |
                   |               | user_id (FK)         |
                   | 1             | achievement_id (FK)  |
        +------------------------+ | desbloqueada_em      |
        |         USERS          | | UNIQUE(user,achiev)  |
        | id (PK)                |-+----------------------+
        | nome / email (UNIQUE)  |  N (user_id)
        | senha_hash             |
        | tipo_usuario           |
        | perfil_publico         |
        | steam_id (UNIQUE,null) |
        +------------------------+
             | 1            | 1
             | (user_id)    | (friend_id)
             | N            | N
        +------------------------+
        |      FRIENDSHIPS       |
        | id (PK)                |
        | user_id  (FK)          |
        | friend_id (FK)         |
        | status                 |
        | UNIQUE(user,friend)    |
        | CHECK(user <> friend)  |
        +------------------------+
```
```
Legenda de cardinalidade:
  USERS 1---N USER_GAMES N---1 GAMES     (lista pessoal)
  GAMES 1---N ACHIEVEMENTS 1---N USER_ACHIEVEMENTS N---1 USERS
  GAMES N---N GENRES / PLATFORMS / DEVELOPERS / PUBLISHERS  (via tabelas de junção)
  USERS 1---N FRIENDSHIPS N---1 USERS    (auto-relacionamento)
  USER_GAMES 1---N REVIEW_LIKES N---1 USERS   (curtidas em reviews)
  USERS 1---N LISTS 1---N LIST_ITEMS N---1 GAMES   (listas customizadas)
  USERS 1---N NOTIFICATIONS   (destinatário; actor_id → USERS; FK friendship_id OU user_game_id)
```

> As tabelas `publishers`/`game_publishers`, `review_likes`, `lists`/`list_items` e
> `notifications` foram acrescentadas após o diagrama ASCII acima; ver §2 e §4 para o
> detalhe dos campos. Para o diagrama visual atualizado, gere a partir de `GameList.dbml`
> em https://dbdiagram.io.
