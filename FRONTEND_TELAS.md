# Telas do Frontend — GameCheck

> Planejamento das telas da SPA React, derivado do backend já entregue
> ([LOG.md](LOG.md)) e do modelo de dados ([ESQUEMA_DADOS.md](ESQUEMA_DADOS.md)).
>
> — a SPA (Vite + React + TS + Mantine) está em
> [frontend/](frontend/); todas as telas abaixo existem. Como rodar:
> [frontend/README.md](frontend/README.md). Detalhes da entrega: [LOG.md](LOG.md).

## Decisões tomadas

| Tema | Escolha |
|---|---|
| Painel admin | **Django Admin permanece** + telas React com o CRUD completo de admin (experiência unificada, mas o Admin fica como rede de segurança) |
| Escopo | **MVP + esqueleto social** — telas sociais navegáveis; ver §3 o que falta no backend para torná-las funcionais |
| Stack | **React + Vite + TypeScript**, consumindo a API DRF; auth por sessão/cookie (+ CSRF) |
| Visual | **Tema escuro**; paleta, tipografia e estilo definidos depois |

---

## 1. Telas do MVP (backend pronto)

### 1.1 Público / não autenticado

| Rota | Tela | Backend | Notas |
|---|---|---|---|
| `/login` | Login | `GET /api/auth/csrf/`, `POST /api/auth/login/` | Guardar CSRF token; redireciona logado |
| `/register` | Cadastro | `POST /api/auth/register/` | Sempre cria usuário `comum` |
| `/` | Home / destaques | `GET /api/games/` | Vitrine de capas; opcional, pode redirecionar p/ `/games` |
| `/games` | Catálogo | `GET /api/games/` (busca + filtros) | Só `publicado` p/ não-admin; filtro por gênero/plataforma; paginação |
| `/games/:id` | Detalhe do jogo | `GET /api/games/:id/` | Sinopse, gêneros, plataformas, dev/publisher, ano, banner/capa |
| `/users/:slug` | Perfil público | `GET /api/profiles/:id/` | URL mostra o **nome** (id trafega via router state, não na URL — ver [LOG.md](LOG.md)); lista + **destaque de platinas**; perfil privado → 404 |

### 1.2 Usuário comum (autenticado)

| Rota | Tela | Backend | Notas |
|---|---|---|---|
| `/my-list` | Minha lista | `GET /api/my-games/` | Abas/filtro por status (jogando, completo, quero_jogar, pausado, abandonado); ordenar por nota/horas |
| (modal) | Adicionar/editar item | `POST/PATCH/DELETE /api/my-games/` | status, nota (0–10), horas, datas início/fim, `platinado`, `review`. Aberto do detalhe do jogo ou da lista |
| `/games/:id` → botão | "Adicionar à minha lista" | `POST /api/my-games/` | Reaproveita o modal acima |
| `/settings/profile` | Editar perfil | `PATCH /api/auth/me/` | nome, bio, **avatar por upload** (arquivo, não URL — JPG/PNG/WEBP/GIF até 2 MB, com preview e "remover"), toggle `perfil_publico`. O `avatar_url` da resposta é a URL de mídia da foto (ver [LOG.md](LOG.md)) |
| `/settings/account` | Conta (email/senha) | *(a confirmar se há endpoint)* | Opcional; talvez só via Django Admin no MVP |

### 1.3 Admin (React + Django Admin)

| Rota | Tela | Backend | Notas |
|---|---|---|---|
| `/admin` | Dashboard | contadores via `GET /api/games/` etc. | Opcional; atalhos p/ o CRUD |
| `/admin/games` | Lista de jogos (inclui rascunhos) | `GET /api/games/?...` | Colunas: título, status_publicacao, ano, steam_appid |
| `/admin/games/new` | Criar jogo | `POST /api/games/` | Multiselect de gêneros/plataformas/devs/publishers |
| `/admin/games/:id/edit` | Editar jogo | `PATCH /api/games/:id/` | Trocar rascunho↔publicado |
| `/admin/games/:id` (delete) | Excluir jogo | `DELETE /api/games/:id/` | **Tratar 409** (jogo em listas — RESTRICT): mostrar aviso claro |
| `/admin/genres` `/platforms` `/developers` `/publishers` | CRUD tabelas de apoio | `/api/genres/`, `/api/platforms/`, `/api/developers/`, `/api/publishers/` | ViewSets REST já existem (`catalog/urls.py`); Django Admin também cobre |

> **Nota admin:** confirmado — `catalog/` já registra ViewSets DRF completos para
> `games`, `genres`, `platforms`, `developers` e `publishers`. Ou seja, **todo o CRUD de
> admin é viável no React** consumindo esses endpoints (escrita restrita a admin pela
> permissão do backend), sem depender do Django Admin.

---

## 2. Esqueleto social (telas navegáveis)

Estas telas entram como estrutura/navegação. Os endpoints de que dependem **já existem**
(ver §3), então podem ser ligadas de fato — não ficam mais só como placeholder.

| Rota | Tela | Depende de |
|---|---|---|
| `/friends` | Amigos: lista + pedidos recebidos/enviados | endpoints de `friendships` |
| `/notifications` | Central de notificações + badge de não lidas | endpoints de `notifications` |
| `/lists` | Minhas listas customizadas | endpoints de `lists`/`list_items` |
| `/lists/:id` | Detalhe/edição de uma lista | idem |
| `/users/:slug` (abas) | Aba "Listas públicas" e botão "Adicionar amigo" no perfil | `lists` + `friendships` |
| `/games/:id` (seção) | Reviews de outros usuários + curtir | `review_likes` + leitura de reviews |

---

## 3. Backend social — **✅ implementado**

Os modelos de `social/` já existiam; os **endpoints, serializers e permissões** foram
implementados em [backend/social/](backend/social/) (ver [LOG.md](LOG.md)). Abaixo, o que
cada recurso expõe hoje. Nenhuma mudança de schema foi necessária.

### 3.1 Amigos (`friendships`) ✅
- **Endpoints:** `POST /api/friendships/` `{friend_id}` (enviar pedido); `GET /api/friendships/`
  com `?estado=amigos|recebidos|enviados`; `POST /api/friendships/:id/aceitar/`;
  `DELETE /api/friendships/:id/` (recusar/cancelar/desfazer).
- **Regras:** auto-pedido e pedido duplicado/invertido são bloqueados (400); leitura
  simétrica (uma linha `aceito` aparece para os dois lados).
- **Efeito colateral:** notificação `pedido_amizade` ao solicitar e `amizade_aceita` ao
  aceitar (atômico com a ação).
- **Permissão:** só os dois envolvidos veem/alteram (`IsFriendshipParticipant`).

### 3.2 Reviews + curtidas (`review_likes`) ✅
- **Leitura de reviews:** `GET /api/reviews/` (feed recente) e `GET /api/reviews/?game=:id`
  (por jogo) — linhas de `user_games` com `review` preenchida; review de perfil privado não
  aparece para terceiros.
- **Curtir/descurtir:** `POST`/`DELETE /api/reviews/:user_game_id/like/` (idempotente; PK
  composta impede curtir 2×).
- **Agregados:** cada review traz `likes_count` e `liked_by_me`.
- **Efeito colateral:** notificação `review_curtida` (exceto ao curtir a própria review).

### 3.3 Listas customizadas (`lists` / `list_items`) ✅
- **CRUD de listas:** `GET/POST/PATCH/DELETE /api/lists/` (só o dono altera);
  `UNIQUE(user, nome)` validado; campo `publica` respeitado.
- **Itens:** `POST /api/lists/:id/items/` `{game_id, ordem?}`,
  `DELETE /api/lists/:id/items/:game_id/`, `PATCH /api/lists/:id/reorder/` `{game_ids: [...]}`.
- **Leitura pública:** `GET /api/lists/?user=:id` lista as `publica = true` de um usuário.

### 3.4 Notificações (`notifications`) ✅
- **Endpoints:** `GET /api/notifications/` (as próprias);
  `GET /api/notifications/nao-lidas/` → `{count}` (badge);
  `POST /api/notifications/:id/marcar-lida/`; `POST /api/notifications/marcar-todas-lidas/`.
- **Geração:** criadas automaticamente pelas ações de §3.1 e §3.2, respeitando o `CHECK` de
  referência exatamente-uma (`friendship_id` XOR `user_game_id` conforme `tipo`).

### 3.5 Apoio ✅
- **Serializers/permissões DRF** de cada recurso no padrão dos apps existentes.
- **Perfil:** `GET /api/profiles/:id/` agora traz `amizade`
  (`eu`/`amigos`/`pedido_enviado`/`pedido_recebido`/`nenhum`/`null`) e `listas_publicas`.
- **Steam** — **✅ implementada** (ver [LOG.md](LOG.md)): botões de login/vínculo
  por Steam (OpenID), autofill do catálogo pela Storefront (botão "Buscar da Steam" no form de
  admin) e sync de biblioteca + conquistas pela Web API (perfil: "Sincronizar biblioteca";
  detalhe do jogo: "Sincronizar conquistas"). Detalhes em
  [CONTEXTO_PROJETO.md](../Atividade_3/CONTEXTO_PROJETO.md) §6.

---

## 4. Estrutura técnica sugerida (a detalhar antes de codar)

- **Vite + React + TypeScript**, `react-router` para as rotas acima.
- **Camada de API** central (fetch/axios) com: base URL da API, envio de cookie de sessão
  (`credentials: 'include'`), leitura/injeção do **CSRF token** em métodos mutantes.
- **Auth context** — `GET /me` no boot para saber se está logado e o `tipo_usuario`.
- **Guards de rota** — `RequireAuth` (usuário comum) e `RequireAdmin` (telas `/admin/*`).
- **Estado de dados** — React Query (ou SWR) para cache de catálogo/lista/perfil.
- **Layout** — navbar com estado de auth, busca do catálogo, badge de notificações
  (via `GET /api/notifications/nao-lidas/`, §3.4), tema escuro.
- **CORS/credenciais** — o backend já configurou CORS para o frontend em dev
  ([LOG.md](LOG.md)); confirmar origem do Vite (`5173`).

## 5. Próximos passos

Backend do MVP **e** do social já estão prontos e testados — todo o consumo das telas
abaixo tem endpoint disponível. Falta só o frontend:

1. Confirmar §4 (roteamento, camada de API/CSRF, guards).
2. Fatiar a implementação: **(a)** scaffold + auth + layout → **(b)** catálogo + detalhe →
   **(c)** minha lista + perfil → **(d)** admin React → **(e)** telas sociais (amigos,
   notificações, listas, reviews) — agora funcionais, não mais placeholder.
