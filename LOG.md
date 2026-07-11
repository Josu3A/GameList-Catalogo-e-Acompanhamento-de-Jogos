# Log de Desenvolvimento — GameList

> Registro cronológico do que foi feito no projeto, com decisões e resultados de
> verificação. Entradas mais recentes no topo.

---

## 2026-07-11 — Backend social (endpoints da extensão de rede social)

### Objetivo

Ativar a parte social ([FRONTEND_TELAS.md](FRONTEND_TELAS.md) §3): os modelos de
`social/` já existiam e estavam migrados, mas faltavam **endpoints, serializers e
permissões** para amigos, reviews+curtidas, listas customizadas e notificações, além de
enriquecer o perfil público. Nenhuma mudança de schema/migração — só a camada de API.

### O que foi criado ([backend/social/](backend/social/))

- **`permissions.py`** — `IsFriendshipParticipant` (só os dois envolvidos veem/alteram a
  amizade) e `IsListOwnerOrReadOnly` (só o dono altera a lista).
- **`serializers.py`** — `UserSummarySerializer` reutilizável; `FriendshipSerializer`
  (bloqueia auto-pedido e pedido duplicado/invertido, leitura simétrica); `ReviewSerializer`
  (sobre `library.UserGame`, com `likes_count`/`liked_by_me` de annotate); `ListSerializer`/
  `ListDetailSerializer` (`UniqueTogetherValidator(user, nome)`, itens ordenados por `ordem`);
  `NotificationSerializer` (bloco `referencia` conforme o `tipo`).
- **`views.py`** —
  - `FriendshipViewSet`: `POST /api/friendships/` (pedido → notificação `pedido_amizade`),
    `GET ?estado=amigos|recebidos|enviados`, `POST /{id}/aceitar/` (→ `amizade_aceita`),
    `DELETE /{id}/` (recusar/cancelar/desfazer).
  - `ReviewViewSet` (read-only + ação): `GET /api/reviews/?game=<id>` (feed/por jogo,
    respeitando visibilidade de perfil), `POST|DELETE /{user_game_id}/like/`
    (idempotente; curtir gera `review_curtida`, exceto na própria review).
  - `ListViewSet`: CRUD do dono + `POST /{id}/items/`, `DELETE /{id}/items/{game_id}/`,
    `PATCH /{id}/reorder/`; `GET /api/lists/?user=<id>` lê as públicas de alguém.
  - `NotificationViewSet` (read-only + ações): `GET /api/notifications/`,
    `GET /nao-lidas/` (badge), `POST /{id}/marcar-lida/`, `POST /marcar-todas-lidas/`.
- **`urls.py`/`admin.py`** — router DRF ligado em `config/urls.py`; admin de `Friendship`,
  `List` e `Notification`.
- **Perfil enriquecido** — `GET /api/profiles/<id>/` passou a devolver `amizade`
  (`eu`/`amigos`/`pedido_enviado`/`pedido_recebido`/`nenhum`/`null`) via
  `Friendship.estado_entre()` e `listas_publicas` do dono.

### Decisões conscientes

| Decisão | Escolha | Motivo |
|---|---|---|
| Reviews | endpoint que **lê `user_games`** com `review` preenchida | a review é coluna de `user_games` (ESQUEMA §1.3); não há entidade própria |
| Notificações | criadas **inline nas ações**, dentro de `transaction.atomic()` | respeita o `CHECK` de referência exatamente-uma (§4.4) e mantém o efeito colateral atômico com a ação |
| Itens de lista | geridos por **actions** (`items`/`reorder`), não por ViewSet próprio | `ListItem`/`ReviewLike` têm PK composta (`CompositePrimaryKey`) — router aninhado fica incômodo |
| Admin de PK composta | `ReviewLike`/`ListItem` **fora do Django Admin** | limitação do Django: modelo com `CompositePrimaryKey` não pode ser registrado nem usado como inline; geridos pela API |
| Amizade simétrica | helper `Friendship.estado_entre()` no modelo | mesma lógica reaproveitada pela validação do pedido e pelo perfil |

### Verificação executada

1. **Migrações**: `makemigrations --check --dry-run` → **No changes detected** (camada só de API).
2. **Testes**: `manage.py test social` → **26/26 OK**; `manage.py test` (suíte completa) →
   **48/48 OK**, cobrindo pedido/aceite/recusa + notificações, leitura simétrica, visibilidade
   de review privada, curtida idempotente + contagem/flag, CRUD de lista só do dono, nome
   duplicado, add/remover/reordenar itens, listas públicas x privadas, contador de não lidas,
   marcar lida, e o `amizade`/`listas_publicas` do perfil.

### Estado ao final

- Endpoints da §3 do [FRONTEND_TELAS.md](FRONTEND_TELAS.md) implementados e testados sobre os
  modelos já existentes; nada de schema mudou.
- Steam (autopreenchimento + sync) segue como trilha separada (CONTEXTO §6).

---

## 2026-07-10 — Backend Django + DRF (MVP completo)

### Objetivo

Implementar o backend do MVP ([CONTEXTO_PROJETO.md](CONTEXTO_PROJETO.md) §5):
autenticação com dois papéis, CRUD do catálogo restrito a admin, CRUD da lista
pessoal restrito ao dono e perfil público com destaque de platinas.

### Decisões tomadas (confirmadas antes da implementação)

| Decisão | Escolha | Motivo |
|---|---|---|
| Arquitetura | API REST (DRF) + Django Admin como painel do admin | Frontend (React) virá depois; o Admin dá o CRUD do catálogo pronto |
| Fonte da verdade do schema | Migrações Django (banco recriado via `migrate`) | O auth do Django exige colunas/hashes próprios; testes ganham banco automático. `db/*.sql` permanece como documentação/entrega |
| Autenticação | Sessão + cookies (nativo) com endpoint CSRF | Simples, funciona com o Admin e a browsable API; atende React em dev via CORS |
| Papéis | `tipo_usuario` (comum/admin) no modelo `User` | Admin ⇒ `is_staff`/`is_superuser`; permissões DRF (`IsAdmin`, `IsAdminOrReadOnly`) leem o campo do domínio |

### O que foi criado ([backend/](backend/))

- **config/** — settings lendo `.env` (PG porta 5433), DRF (sessão, paginação,
  django-filter), CORS para o futuro frontend.
- **accounts/** — `User` customizado (`AbstractBaseUser`) mapeando a tabela `users`
  (hash do Django gravado em `senha_hash`); endpoints `register/login/logout/me/csrf`;
  registro público sempre cria usuário comum; Django Admin de usuários.
- **catalog/** — `Game` + `Genre/Platform/Developer/Publisher` (M2M) + `Achievement`;
  `/api/games/` com leitura pública (não-admin só vê `publicado`), escrita só admin,
  busca e filtros; `DELETE` de jogo presente em listas responde **409** (RESTRICT).
- **library/** — `UserGame` com todas as constraints nomeadas (`uq_user_game`,
  `ck_user_games_*`) e índice parcial de platinas; `/api/my-games/` sempre filtrado
  pelo dono (payload nunca escolhe o usuário); `/api/profiles/<id>/` com seção
  `platinas`; perfil privado responde 404 para terceiros.
- **social/** — modelos fiéis das extensões (friendships, review_likes com PK
  composta, lists/list_items, notifications com o CHECK de referência
  exatamente-uma). Sem endpoints — extensão futura.
- **Triggers** — migrações `RunSQL` recriam `set_updated_at()` e os 4 triggers de
  `updated_at`, mantendo a decisão da entrada anterior.
- **seed_demo** — `python manage.py seed_demo` porta o [db/seed.sql](db/seed.sql)
  com senhas reais (todos os usuários demo: `senha123`), resolvendo o ⚠️ dos
  placeholders de `senha_hash`.

### Divergências conscientes em relação a db/schema.sql

| Divergência | Motivo |
|---|---|
| `users.last_login` (nullable) a mais | Exigência do `AbstractBaseUser` do Django |
| Junções `game_*` com coluna `id` própria + `UNIQUE(game_id, X_id)` em vez de PK composta | M2M padrão do Django (admin com `filter_horizontal` funciona pronto); `review_likes`/`list_items` mantêm PK composta via `CompositePrimaryKey` |
| `ON DELETE` (CASCADE/RESTRICT/SET NULL) aplicado pelo ORM, não no DDL | Comportamento do Django; a semântica decidida no ESQUEMA_DADOS §6 é a mesma, garantida pela aplicação (testado) |
| Índices de FK com nomes autogerados pelo Django | FKs já ganham índice automático; os índices com forma especial mantêm o nome original (`idx_user_games_platinados`, `idx_notifications_user_lida`) |
| Tabelas de sistema do Django (`django_*`, `auth_*`) a mais | Sessões, admin e migrações |

### Verificação executada

1. **Testes**: `manage.py test` → **22/22 OK** cobrindo os critérios de aceitação do
   CONTEXTO §4 (comum não altera catálogo; admin CRUD completo; duplicata e nota 11
   rejeitadas; rascunho não entra em lista; ninguém edita lista alheia; perfil
   privado bloqueado; login inválido rejeitado).
2. **Banco recriado**: `DROP/CREATE DATABASE gamelist` + `migrate` + `seed_demo` →
   as **18 tabelas** do domínio e os **4 triggers** presentes (conferido via psql).
3. **E2E na API real** (runserver + HTTP): 17 cenários **PASS** — login/logout,
   403 para comum criar jogo, 201/400 na lista pessoal, platina do Hades no perfil
   público, CRUD do admin (201/200/204) e 409 ao remover jogo presente em listas.
4. **Django Admin**: admin@gamelist.dev acessa o painel de jogos (200); usuária
   comum é redirecionada ao login (302).

### Estado ao final

- Backend MVP funcional em [backend/](backend/) (instruções no
  [backend/README.md](backend/README.md)); banco `gamelist` recriado e populado.
- Próximos passos sugeridos: frontend (React consumindo a API) e, depois, as
  extensões (amigos, integração Steam) sobre os modelos já existentes.

---

## 2026-07-10 — Criação do banco de dados PostgreSQL

### Objetivo

Traduzir o esquema de dados já modelado ([ESQUEMA_DADOS.md](ESQUEMA_DADOS.md) e
[GameList.dbml](GameList.dbml)) para DDL do PostgreSQL, gerando os scripts que criam o
banco do zero, e validar tudo num servidor real.

### Decisões tomadas (confirmadas antes da implementação)

| Decisão | Escolha | Motivo |
|---|---|---|
| Escopo do script | Todas as 18 tabelas (MVP + catálogo normalizado + Steam + rede social) | O banco já nasce pronto para as extensões, sem migrações futuras; tabelas vazias não atrapalham o MVP |
| Manutenção de `updated_at` | Trigger no banco (`set_updated_at()`) | PostgreSQL não atualiza o campo sozinho em UPDATE; com trigger o comportamento independe do backend escolhido |
| Dados iniciais | Arquivo `seed.sql` separado do schema | Facilita demonstrar o CRUD na atividade sem misturar dados com estrutura |
| Enums | `VARCHAR` + `CHECK` (não `ENUM` nativo) | Decisão já documentada em ESQUEMA_DADOS.md §Convenções e §6; o DBML usa enum nativo só para o diagrama visual |

### Arquivos criados

**[db/schema.sql](db/schema.sql)** — estrutura completa, em transação única (`BEGIN/COMMIT`):

1. Função `set_updated_at()` (plpgsql).
2. Núcleo MVP: `users`, `games`, `user_games`.
3. Catálogo normalizado: `genres`, `platforms`, `developers`, `publishers` + 4 junções N:N
   (`game_genres`, `game_platforms`, `game_developers`, `game_publishers`).
4. Integração Steam (extensão futura): `achievements`, `user_achievements`.
5. Rede social: `friendships`, `review_likes`, `lists`, `list_items`, `notifications`.
6. Índices do ESQUEMA_DADOS §5, incluindo o índice parcial
   `user_games(user_id) WHERE platinado = true` (destaque de platinas no perfil).
7. Triggers de `updated_at` nas 4 tabelas que têm o campo (`users`, `games`,
   `user_games`, `lists`).

Fidelidade ao esquema: constraints nomeadas (`ck_*`, `uq_*`), `ON DELETE` conforme a
tabela de decisões (§6) — FKs de usuário em `CASCADE`, `user_games.game_id` e
`list_items.game_id` em `RESTRICT`, `notifications.actor_id` em `SET NULL` — e o `CHECK`
de referência exatamente-uma em `notifications` (§4.4). `COMMENT ON TABLE` com as notas
do DBML.

**[db/seed.sql](db/seed.sql)** — dados de demonstração:

- 1 admin + 2 usuários comuns (Ana e Bruno). ⚠️ `senha_hash` são **placeholders**
  marcados no arquivo; a aplicação deve gerar hashes reais (bcrypt/argon2).
- 8 gêneros, 6 plataformas, 5 developers, 5 publishers.
- 5 jogos publicados com `steam_appid` reais (Elden Ring 1245620, Hades 1145360,
  Stardew Valley 413150, Hollow Knight 367520, Celeste 504230), ligados via junções.
- Listas pessoais cobrindo os 5 status; 1 platina com review (Ana/Hades) e 1 entrada
  vinda de `steam_sync` (Bruno/Stardew), para demonstrar os critérios de aceitação.
- Extensões: 1 curtida de review, 1 amizade aceita e as 3 notificações (uma de cada
  tipo, respeitando o `CHECK` de referência).
- IDs explícitos + `setval` das sequences, para os scripts serem reproduzíveis.

### Verificação executada

Ambiente: a máquina tem **PostgreSQL 16 (porta 5432)** e **PostgreSQL 18 (porta 5433)**
rodando como serviço. O banco foi criado no **PG 18, porta 5433** (a instância 16 tem
credenciais diferentes). ➜ **Ao configurar o backend (Django), usar porta 5433.**

Passos executados via `psql` (`C:\Program Files\PostgreSQL\18\bin\psql.exe`):

```
CREATE DATABASE gamelist;
psql -d gamelist -f db/schema.sql   → sem erros (com ON_ERROR_STOP=1)
psql -d gamelist -f db/seed.sql    → sem erros (com ON_ERROR_STOP=1)
```

Sanity checks (script temporário; testes destrutivos em transação com `ROLLBACK`):

| # | Teste | Esperado | Resultado |
|---|---|---|---|
| 1 | Contagem de tabelas em `public` | 18 | ✅ 18 |
| 2 | `INSERT` com `nota = 11` | rejeitar | ✅ `ck_user_games_nota` |
| 3 | `INSERT` com `status = 'platinando'` | rejeitar | ✅ `ck_user_games_status` |
| 4 | Jogo duplicado na lista do mesmo usuário | rejeitar | ✅ `uq_user_game` |
| 5 | Amizade consigo mesmo | rejeitar | ✅ `ck_friendship_nao_reflexiva` |
| 6 | Notificação `review_curtida` apontando para `friendship_id` | rejeitar | ✅ `ck_notifications_referencia` |
| 7 | `UPDATE` em `users` atualiza `updated_at` | sim | ✅ trigger funcionou |
| 8 | `DELETE` de jogo presente em `user_games` | bloquear | ✅ RESTRICT |
| 9 | `DELETE` de usuário limpa `user_games` e `review_likes` dele | cascatear | ✅ CASCADE (com rollback) |
| 10 | Consulta de platinas para o perfil | 1 linha | ✅ "Ana Souza — Hades — 9.5 — 112.0h" |

### Estado ao final

- Banco `gamelist` criado e populado no PostgreSQL 18 local (porta 5433).
- Scripts em [db/](db/) prontos para recriar o banco em qualquer ambiente
  (instruções de uso no cabeçalho de cada arquivo).
- Próximos passos sugeridos: iniciar o backend (Django + DRF, conforme
  [CONTEXTO_PROJETO.md](CONTEXTO_PROJETO.md) §7) apontando para este banco, com
  autenticação e os dois papéis de usuário.
