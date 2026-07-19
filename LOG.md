# Log de Desenvolvimento — GameList

> Registro cronológico do que foi feito no projeto, com decisões e resultados de
> verificação. Entradas mais recentes no topo.

---

## Rebrand "GameCheck": logo tratada, nome, paleta e fundo do app

### Objetivo

Rebatizar o produto de **GameList** para **GameCheck** e aplicar a **logo nova** (entregue como
um app icon 1254×1254 com fundo preto). Pedidos, em ordem: **deixar a logo usável** (remover o
fundo), **renomear a imagem**, **alinhar as cores do tema** à logo e **mudar o fundo do app**
para casar com ela.

### O que mudou (só frontend)

- **Logo tratada** (fundo removido, transparência real) — a arte é um "G" formado por um gamepad,
  com gradiente **violeta→azul**, D-pad branco e 4 botões coloridos, sobre um card azul-marinho
  arredondado que estava emoldurado por preto puro. Separei fundo × arte pelo **valor**
  `V=max(R,G,B)` (o preto externo é `0`, o card ~`28`, a arte é clara/saturada):
  - `../gamecheck-logo.png` (raiz do workspace, **renomeando** o `ChatGPT_Image_*.png` original,
    que foi apagado) — master em alta, só o glyph sobre transparência.
  - [frontend/public/logo.png](frontend/public/logo.png) — glyph limpo 512px, usado na navbar.
  - [favicon.png](frontend/public/favicon.png) (64), [apple-touch-icon.png](frontend/public/apple-touch-icon.png)
    (180) e [icon-512.png](frontend/public/icon-512.png) — **ícone de app reconstruído**: o recorte
    direto do card trazia um "halo" cinza (brilho radial do original), então recompus o glyph limpo
    sobre um card com gradiente (`#16172E`→`#0A0B1B`) e cantos arredondados (~22,5%).
- **Nome GameList → GameCheck** — [Navbar.tsx](frontend/src/components/Navbar.tsx) (ícone genérico
  `IconDeviceGamepad2` → `<img src="/logo.png">` + texto "GameCheck"); título e favicons em
  [index.html](frontend/index.html); H1 do [frontend/README.md](frontend/README.md). (Nome do
  pacote/pasta/repo `GameList` **não** mudou — só a marca visível.)
- **Cores da marca** em [theme.ts](frontend/src/theme.ts) — paleta **`brand`** (10 tons) derivada
  do gradiente violeta `#7137F3`→azul `#1584FD` do "G", como `primaryColor` (`primaryShade`
  `{ light: 6, dark: 6 }`); `defaultGradient` `#7137F3`→`#1584FD` (135°) espelhando o "G"→seta.
- **Fundo do app** — a escala **`dark`** do Mantine foi **retintada para azul-marinho**, casando
  com o card da logo, **mantendo a mesma luminância** do padrão (contraste do texto preservado):
  fundo da página `dark[7]=#111327` (antes o cinza `#1A1B1E`), superfícies/cards `dark[6]=#1A1D36`,
  tom mais profundo `dark[9]=#090B1A`.

### Decisões conscientes

| Decisão | Escolha | Motivo |
|---|---|---|
| Remover o fundo | **glyph transparente** como logo principal + **tile reconstruído** para favicon | glyph integra na navbar/fundo escuro; o tile do recorte cru ficava com halo cinza — reconstruir dá um ícone nítido |
| Separação fundo × arte | limiar sobre o **valor** `max(R,G,B)` (não por cor) | preto (`0`) e card navy (`~28`) são escuros; a arte é clara/saturada — o valor separa com borda suave, sem chave de croma |
| Onde guardar assets web | `frontend/public/` (servido na raiz pelo Vite) | `/logo.png`, `/favicon.png` etc. sem import/bundle; simples de referenciar no `index.html`/JSX |
| Fundo do app | **retintar a escala `dark`** (mesma L, hue navy) em vez de CSS global | é o caminho idiomático do Mantine v7; preserva contraste e cobre header/cards/dropdowns de uma vez |
| Escopo do "nome" | trocar só a **marca visível**, não pacote/pasta/repo | evita quebrar imports, scripts e histórico do git por uma mudança cosmética |

### Verificação executada

1. **Tipos:** `tsc --noEmit` → **sem erros** (após a remoção do ícone antigo, o tema tipado com
   `MantineColorsTuple` e a retinta do `dark`).
2. **Inspeção visual dos assets gerados:** glyph transparente limpo (sem halo) e ícone de app
   nítido com cantos arredondados — conferidos abrindo os PNGs.

### Estado ao final

- Marca **GameCheck** aplicada: logo transparente na navbar, favicon/ícones de app, título da aba,
  paleta violeta→azul e fundo navy — identidade coesa com a logo.
- Imagem original renomeada para `gamecheck-logo.png` (master transparente); o `ChatGPT_Image_*.png`
  foi removido.

---

## Estados vazios com botão de ação (perfil, minha lista, listas)

### Objetivo

As telas com **contadores zerados** (perfil de quem ainda não adicionou jogos/listas, "Minha
lista" vazia, "Minhas listas" vazia) mostravam só um ícone + um texto ("Nada por aqui ainda.",
"Nenhuma lista pública.") — becos sem saída, sem indicar o próximo passo. Pedido: **adicionar
botões de ação** ("adicionar jogo", "criar uma lista" etc.) para as telas vazias convidarem à ação.

### O que mudou (só frontend)

- **Componente compartilhado** [GameCard.tsx](frontend/src/components/GameCard.tsx): o
  `EmptyState` ganhou uma prop opcional **`action`** (`React.ReactNode`), renderizada abaixo do
  texto num `Group` centralizado. Sem `action`, o visual continua idêntico ao anterior.
- **Perfil** [ProfilePage.tsx](frontend/src/pages/profile/ProfilePage.tsx) (a tela da imagem):
  no **próprio perfil** (`amizade === 'eu'`), a aba **Jogos** vazia mostra **"Adicionar jogo"**
  (→ `/games`) e a aba **Listas** vazia mostra **"Criar uma lista"** (→ `/lists`). `GamesGrid`
  recebeu um `emptyAction` opcional para carregar o botão só na aba de jogos (a seção de platinas
  reusa o mesmo grid e nunca renderiza estado vazio).
- **Minha lista** [MyListPage.tsx](frontend/src/pages/library/MyListPage.tsx): estado vazio ganhou
  **"Explorar catálogo"** (→ `/games`), reforçando a dica que já estava no texto.
- **Minhas listas** [ListsPage.tsx](frontend/src/pages/social/ListsPage.tsx): estado vazio ganhou
  **"Criar lista"** (abre o modal de nova lista). Para **não duplicar** o botão, o "Nova lista" do
  topo passou a aparecer **só quando já existem listas** — vazio mostra só o CTA centralizado.

### Decisões conscientes

| Decisão | Escolha | Motivo |
|---|---|---|
| Só o dono vê os atalhos | perfil alheio vazio segue **sem** botão (`isMe = amizade === 'eu'`) | ninguém adiciona jogo/lista na biblioteca de outra pessoa — o botão só faz sentido no próprio perfil |
| "Adicionar jogo" → catálogo | leva a `/games`, não a `/my-list` | é dali que se adiciona à lista (via detalhe do jogo); mesma dica do estado vazio de "Minha lista" |
| Onde colocar o botão | prop `action` no `EmptyState` já existente | um único ponto para todos os estados vazios, sem duplicar layout; retrocompatível (prop opcional) |

### Verificação executada

1. **Tipos:** `tsc --noEmit` → **sem erros**.

### Estado ao final

- Telas vazias de perfil (próprio), "Minha lista" e "Minhas listas" agora trazem um botão que
  leva ao próximo passo; perfil de terceiros vazio permanece só informativo.

---

## Adicionar amigo (busca de usuários por nome) + filtro na lista de amigos

### Objetivo

A tela de Amigos ([/friends](frontend/src/pages/social/FriendsPage.tsx)) só listava amizades e
pedidos — não havia como **encontrar alguém para adicionar**. Faltava um endpoint para buscar
usuários. Adicionar um botão que abre a busca e dispara o pedido de amizade e, separadamente, um
**filtro por nome** sobre os amigos já adicionados (busca ≠ filtro: o botão *adiciona* gente nova;
o filtro *procura* dentro de quem você já tem).

### O que mudou

- **Backend (`social/`)** — novo endpoint **`GET /api/users/search/?q=`** para achar usuários e
  enviar pedido de amizade:
  - [views.py](backend/social/views.py): `UserSearchView` (`ListAPIView`, exige autenticação).
    Filtra **por nome** (`nome__icontains`), só **perfis públicos** (perfil privado não é
    descoberto, como no `ProfileView`) e nunca inclui o próprio usuário; termo com menos de 2
    caracteres devolve vazio.
  - [serializers.py](backend/social/serializers.py): `UserSearchSerializer` estende o
    `UserSummarySerializer` e acrescenta `amizade` (via `Friendship.estado_entre`), para o botão
    escolher entre *Adicionar* / *Pedido enviado* / *Pedido recebido* / *Amigos*.
  - [urls.py](backend/social/urls.py): rota `users/search/` registrada antes do router.
- **Frontend** — [FriendsPage.tsx](frontend/src/pages/social/FriendsPage.tsx): botão
  **"Adicionar amigo"** no topo abre um modal com busca (debounce 300 ms) que lista os resultados;
  cada linha mostra *Adicionar* (reusa `sendFriendRequest`) ou um selo conforme o estado da amizade.
  Na aba **Amigos**, campo **"Filtrar amigos por nome"** filtra a lista localmente (as abas de
  pedidos não recebem filtro). Extraí um `renderRow` para acomodar o filtro sem aninhar o JSX.
  [api/social.ts](frontend/src/api/social.ts): `searchUsers`; [types/index.ts](frontend/src/types/index.ts):
  `UserSearchResult` (`UserSummary` + `amizade`).

### Decisões conscientes

| Decisão | Escolha | Motivo |
|---|---|---|
| Só nome (sem e-mail) | busca por `nome__icontains` apenas | pedido do grupo; e-mail não é identificador público — a resposta nunca expõe e-mail (só `id`/`nome`/`avatar_url`/`amizade`) |
| Descoberta | só **perfis públicos**, exclui a si mesmo | mesma privacidade do `ProfileView` (perfil privado nem revela existência) |
| Botão × filtro | botão **adiciona** (busca no servidor); filtro **procura nos já adicionados** (client-side) | separa os dois fluxos que a UI antes confundia num só "buscar amigos" |
| Estado no resultado | `amizade` em cada item da busca | o botão decide entre adicionar/aguardar sem uma segunda chamada |

### Verificação executada

1. **Backend:** `manage.py test social` → **31/31 OK** (26 anteriores + 5 novos em
   `BuscaAmigosTests`: exige autenticação; ignora a si mesmo e perfis privados; traz o estado da
   amizade; termo curto vazio; e-mail **não** encontra ninguém). `manage.py check` sem erros.
2. **Frontend:** `tsc --noEmit` → **sem erros**.

### Estado ao final

- Tela de Amigos com "Adicionar amigo" (busca por nome + pedido) e filtro por nome na aba Amigos.
- Pendente/decisão do grupo: o filtro é **client-side** sobre a página atual (amizades vêm
  paginadas em 20, e a aba não pagina) — se alguém passar de 20 amigos, o filtro só alcança os 20
  primeiros; tratar com busca no servidor fica como evolução.

---

## 100 jogos famosos da Steam no catálogo + migração para o seed (offline)

### Objetivo

Preencher o catálogo com os ~100 jogos mais famosos da Steam **e** deixar isso no `seed`,
para o banco já nascer com esse catálogo ao inicializar — **sem depender da rede** na
inicialização (a Storefront tem limite de taxa e ~2 min de latência para 100 chamadas).

### O que mudou

- **Comando live** [seed_steam_top.py](backend/catalog/management/commands/seed_steam_top.py)
  (+ `__init__.py` do pacote): lista fixa de **100 AppIDs** famosos (deduplicada); para cada um
  chama `catalog.steam.fetch_appdetails` (Storefront, sem chave), resolve as taxonomias por
  `get_or_create` e faz `update_or_create` do `Game` como **publicado**. Idempotente (casa por
  `steam_appid`). Flags: `--limit`, `--delay` (com retentativa/backoff), `--lang`, `--update`,
  `--dry-run` e **`--offline`** (semeia do snapshot, sem rede).
- **Snapshot versionado** [catalog/data/steam_top_games.json](backend/catalog/data/steam_top_games.json):
  os 100 jogos "congelados" (título, ano, sinopse PT, capa/banner, taxonomias por nome),
  exportados do banco após um `seed_steam_top --update` (dados uniformes da Steam).
- **Loader compartilhado** [catalog/seed_data.py](backend/catalog/seed_data.py): `load_top_games()`
  lê o snapshot; `apply_games()`/`apply_game()` inserem/atualizam casando por `steam_appid` e
  resolvem taxonomias — reusado pelo `seed_steam_top --offline` **e** pelo `seed_demo`.
- **Seed migrado** [seed_demo.py](backend/library/management/commands/seed_demo.py): saíram as
  listas inline de 5 jogos/taxonomias; agora carrega os **100 do snapshot offline** e monta as
  listas pessoais por `appid` (os 5 jogos da demo estão entre os 100). Users/listas/amizade/
  notificações seguem iguais.
- **Doc** [backend/README.md](backend/README.md): nova seção "Carregar o catálogo" + Setup e
  Estrutura atualizados.

### Como carregar (não há "config" no app)

**Não existe nada a registrar em `settings.py`** (nem env var, nem `INSTALLED_APPS`): o
snapshot é versionado no repo e lido direto pelo app `catalog` por caminho relativo ao pacote.
"Carregar" = **rodar o comando** (todos idempotentes, casam por `steam_appid`):

```
python manage.py migrate                      # cria as tabelas
python manage.py seed_demo                    # init: 3 usuários + 100 jogos (offline) + demo
python manage.py seed_steam_top --offline     # só o catálogo, do snapshot, sem rede
python manage.py seed_steam_top               # (online) cria/atualiza os 100 pela Steam
python manage.py seed_steam_top --update      # refaz o snapshot-fonte com dados atuais da Steam
```

Num ambiente novo, o catálogo entra sozinho no passo `seed_demo` do setup. Auto-rodar o seed
no startup do app (`AppConfig.ready()`) foi **descartado** de propósito — roda a cada
processo/worker, exige o banco pronto e dá corrida; o idiomático é o comando no provisionamento
(ou, se quiserem automatizar, um hook `post_migrate`/entrypoint — não feito).

### Verificação executada

1. **Run online completo:** `seed_steam_top` → **92 criados, 8 já existentes, 0 falhas** (de
   100); todos os AppIDs resolveram na Storefront. Depois `--update` uniformizou os dados.
2. **Snapshot:** exportado e validado — **100 entradas, 100 appids únicos**, nenhum sem
   título/gênero; JSON UTF-8 (ex.: "Ação").
3. **Init offline num banco limpo (teste):** `library.tests.SeedDemoTests` roda `seed_demo`
   no `test_gamelist` (migra do zero) → **exatamente 100 jogos publicados** + 3 usuários + a
   platina da Ana; segundo run **idempotente** (continua 100/3). Sem rede.
4. **Suíte completa:** `manage.py test` → **74/74 OK** (72 + 2 novos do seed).
5. **`manage.py check`** e **`seed_steam_top --offline --dry-run`** sem erros.

### Estado ao final

- Banco de dev já com **101 jogos** (100 do catálogo + 1 avulso pré-existente). Init limpo
  (`migrate` + `seed_demo`) traz os 100 offline, instantâneo e reproduzível.
- `db/seed.sql` (a "entrega" SQL) **não** foi tocado — segue com os 5 jogos originais; se o
  grupo quiser, dá para regenerá-lo a partir do snapshot.

---

## Avatar por upload na edição de perfil (arquivo, não URL)

### Objetivo

Na edição de perfil, o avatar deixava de ser um campo de **URL** e passa a ser **upload de
arquivo**, com limites. O backend guarda só o **caminho** do arquivo no banco; o usuário
**nunca vê o caminho** — vê a foto (a API devolve uma URL de mídia).

### O que mudou

- **`accounts/`** — [models.py](backend/accounts/models.py): `avatar_url` deixou de ser
  `URLField` e virou **`ImageField`** (`upload_to=avatars/<uuid>.<ext>`, nome opaco por uuid,
  `FileExtensionValidator` JPG/PNG/WEBP/GIF). **A coluna segue `VARCHAR(500)`** — a migração
  [0003](backend/accounts/migrations/0003_alter_user_avatar_url.py) é só troca de tipo lógico,
  **sem DDL** no Postgres. [serializers.py](backend/accounts/serializers.py): `avatar_url` como
  `ImageField` (upload no `multipart`, `null` limpa) + validação de **2 MB**; removido do
  `RegisterSerializer` (avatar é definido depois, no perfil). [views.py](backend/accounts/views.py):
  `UserSerializer` agora recebe `context={'request'}` (URL de mídia **absoluta**); o vínculo Steam
  **baixa** o avatar do perfil Steam e salva como mídia local (best-effort) em vez de gravar a URL
  externa — todos os avatares viram arquivo local.
- **`library/`** — [views.py](backend/library/views.py): o `avatar_url` do perfil público vira
  `request.build_absolute_uri(user.avatar_url.url)` (ou `None`).
- **`config/`** — [settings.py](backend/config/settings.py): `MEDIA_URL`/`MEDIA_ROOT` +
  teto de upload (2,5 MB); [urls.py](backend/config/urls.py) serve `MEDIA_ROOT` em `DEBUG`.
  `Pillow~=11.0` em [requirements.txt](backend/requirements.txt) (exigido pelo `ImageField`).
- **Frontend** — [EditProfilePage.tsx](frontend/src/pages/profile/EditProfilePage.tsx): campo de
  URL trocado por **upload** (`FileButton`) com **preview** (`Avatar` + `URL.createObjectURL`),
  botão **Remover**, hint de formatos/limite e validação client-side espelhando o backend.
  [auth.ts](frontend/src/api/auth.ts): `updateMe` monta `FormData` quando há arquivo, ou envia
  `avatar_url: null` para remover. Nada nas telas de exibição mudou: `avatar_url` continua sendo a
  URL que os `<Avatar>` (navbar, perfil, reviews, amigos, notificações) já consomem.

### Decisões conscientes

| Decisão | Escolha | Motivo |
|---|---|---|
| Onde guardar | **Reaproveitar `avatar_url`** como `ImageField` (mesma coluna) | zero mudança de DDL; todos os serializers/telas já usam `avatar_url` — vira URL de mídia sozinho |
| Nome do arquivo | `avatars/<uuid>.<ext>` | caminho **opaco**; não expõe nome original nem id — o usuário só vê a foto |
| Avatar da Steam | **baixar** e salvar como mídia local | `ImageField` não guarda URL externa; mantém o recurso e deixa tudo local/consistente |
| Limites | imagem válida (Pillow) + extensão + **2 MB** | validado no serializer **e** no cliente; `ImageField` já rejeita não-imagem |
| Registro | avatar **fora** do cadastro | avatar é definido na edição de perfil, por upload — não há upload no registro |

### Verificação executada

1. **Migração:** `makemigrations` gerou só `AlterField` (varchar 500 → varchar 500);
   `makemigrations --check --dry-run` → **No changes**.
2. **Testes:** `manage.py test` → **72/72 OK** (68 anteriores + 4 novos: upload válido salva o
   arquivo e devolve URL de mídia; não-imagem → 400; > 2 MB → 400; `null` limpa o avatar).
   MEDIA_ROOT isolado por `override_settings` + tempdir.
3. **Frontend:** `tsc --noEmit` → **sem erros**.

### Estado ao final

- Edição de perfil sobe o avatar por arquivo; o banco guarda o caminho, a UI mostra a foto.

---

## Capas verticais da biblioteca Steam (catálogo, detalhe e fundo do topo)

### Objetivo

As capas apareciam **cortadas** no catálogo e na página do jogo. Causa: o `capa_url`
guardava o *capsule horizontal* (`capsule_image`, ~616×353) e o `banner_url` o *header*
pequeno (`header_image`, 460×215) — ambos recortam feio no card vertical (3:4) e na faixa
larga do topo. A Steam expõe artes próprias da biblioteca, montáveis a partir do `appid`:
**`library_600x900`** (capa vertical) e **`library_hero`** (fundo largo ~1920×620). Passar a
usá-las por padrão no catálogo, no detalhe **e** no fundo do topo.

### O que mudou

- **`catalog/`** — [steam.py](backend/catalog/steam.py): helpers `library_cover_url()` /
  `library_hero_url()` (base `STEAM_CDN`) e o autofill (`fetch_appdetails`) passou a gravar a
  capa vertical + fundo largo por padrão (caindo para capsule/header se faltarem).
  [models.py](backend/catalog/models.py): propriedades `capa_vertical_url` e `banner_hero_url`
  no `Game`, **derivadas do `steam_appid` em tempo de leitura** (caem para `capa_url`/`banner_url`
  quando não há appid). [serializers.py](backend/catalog/serializers.py): os dois campos como
  read-only no `GameSerializer`.
- **`library/`** — [serializers.py](backend/library/serializers.py): `GameSummarySerializer`
  (usado nos cards dentro de listas/perfis) ganhou `capa_vertical_url`.
- **Frontend** — [types/index.ts](frontend/src/types/index.ts) espelhando os campos novos;
  [GameCard.tsx](frontend/src/components/GameCard.tsx) e
  [GameDetailPage.tsx](frontend/src/pages/catalog/GameDetailPage.tsx) usam a capa vertical
  (com `fallbackSrc` para o capsule) e o detalhe troca o fundo do topo para o `library_hero`
  (altura 220→260 para não cortar).

### Decisões conscientes

| Decisão | Escolha | Motivo |
|---|---|---|
| Onde derivar | **Em tempo de leitura** (propriedade/serializer), não em migração de dados | Conserta sozinho os jogos **já cadastrados** (todos têm `steam_appid`); nada de reimportar nem migrar |
| Campos brutos | `capa_url`/`banner_url` seguem editáveis e são **fallback** | A edição do admin continua nos campos originais; a arte da biblioteca é só exibição |
| Robustez | `fallbackSrc={capa_url}` no `<Image>` | Se `library_600x900` faltar/404 num app, cai no capsule — nenhum card fica sem imagem |
| Sem migração | Só `@property` + campos read-only | Nenhuma coluna nova; `makemigrations` não muda nada |

### Verificação executada

1. **URLs reais (curl):** `library_600x900.jpg`, `library_hero.jpg` e `library_600x900_2x.jpg`
   → **200** para os appids do seed (Elden Ring 1245620, Hades 1145360, Stardew 413150) nos
   três hosts de CDN (`steamcdn-a.akamaihd.net`, `cdn`/`shared.cloudflare.steamstatic.com`).
2. **Testes:** `manage.py test catalog library` → **27/27 OK** (fields read-only não quebraram
   permissões nem o autofill mockado).
3. **Serialização:** `GameSerializer`/`GameSummarySerializer` de um `Game(appid=1245620)`
   devolvem `capa_vertical_url`/`banner_hero_url` com as URLs da biblioteca; sem appid, caem
   para os campos brutos.
4. **Frontend:** `tsc --noEmit` → **sem erros**.

### Estado ao final

- Catálogo, detalhe e fundo do topo usam as artes verticais/largas da biblioteca Steam por
  padrão; jogos já cadastrados corrigidos automaticamente (derivação por `appid`, sem migração).
- Jogo sem `steam_appid` (ou sem a arte publicada) cai no `capa_url`/`banner_url` cadastrado.

---

## Integração com a Steam (login/vínculo, autofill do catálogo, sync de biblioteca e conquistas)

### Objetivo

Implementar a extensão Steam ([CONTEXTO_PROJETO.md](../Atividade_3/CONTEXTO_PROJETO.md) §6):
**botões de login por Steam**, **autopreenchimento do catálogo pela API da Steam**
(publishers, desenvolvedoras, imagens, gêneros, plataformas) e — decisão do grupo — também
**sync da biblioteca do usuário e conquistas**. O banco já estava pronto (todos os models
existiam e estavam migrados); **nenhuma migração de schema foi necessária**.

### Decisões (confirmadas antes de codar)

| Decisão | Escolha | Motivo |
|---|---|---|
| Login Steam | **Só vincula/loga — nunca cria conta** | contas nascem por e-mail/senha; o `steam_id` é vinculado depois. O botão de login por Steam loga quem já vinculou; SteamID desconhecido volta ao login com aviso (`?steam=nolink`). Sem contas-sombra |
| Escopo | **Tudo, incluindo conquistas** | login/vínculo + autofill + sync de biblioteca (jogos+horas) + sync de conquistas (esquema + desbloqueadas + sugestão de platinado) |
| OpenID | **implementação leve própria** (sem allauth) | o `User` é `AbstractBaseUser` com login por e-mail; adaptar allauth custaria mais que os ~40 linhas de OpenID 2.0 |
| Chave Steam | `STEAM_API_KEY` só no backend (`.env`) | OpenID e Storefront são keyless; Web API (biblioteca/conquistas/persona) exige a chave |
| Autofill | **prévia que preenche o form** (não cria o Game) | mantém o fluxo "rascunho → autopreenche → admin revisa → publica" (ESQUEMA §1.2) |

### O que mudou

- **Config:** `requests~=2.32` em [requirements.txt](backend/requirements.txt);
  `STEAM_API_KEY` e `FRONTEND_URL` em [settings.py](backend/config/settings.py) + `.env(.example)`.
- **`accounts/`** — novo [steam.py](backend/accounts/steam.py) (OpenID 2.0:
  `build_login_url`/`verify_response`; + `get_player_summary`). Views `steam_login`/
  `steam_callback` (redirect) e `SteamDisconnectView` (POST); rotas `steam/login|callback|disconnect`.
  Callback: **logado→vincula** (bloqueia `steam_id` de outra conta), **anônimo→loga** se já
  vinculado, senão avisa. Preenche avatar via persona se estiver vazio.
- **`catalog/`** — novo [steam.py](backend/catalog/steam.py) (Storefront `appdetails` → campos
  + listas). Ação `POST /api/games/steam-preview/` (só admin): resolve taxonomias por
  `get_or_create` (padrão do `seed_demo`) e devolve os campos + `[{id,nome}]` + `existing_game_id`.
- **`library/`** — novo [steam.py](backend/library/steam.py) (Web API: `get_owned_games`,
  `get_schema_for_game`, `get_player_achievements`). Ações no `UserGameViewSet`:
  `POST /api/my-games/steam-sync/` (casa por `steam_appid`, grava `fonte='steam_sync'` +
  horas, não sobrescreve entradas manuais) e `POST /api/my-games/steam-achievements/`
  (`{game_id}`: popula `Achievement`/`UserAchievement`, calcula % e sugere `platinado` a 100%).
- **Frontend** — `API_BASE_URL` exportado; `steamLoginUrl`/`disconnectSteam` (auth),
  `steamPreview` (games), `steamSync`/`steamAchievements` (library) + tipos. Botão
  **SteamLoginButton** no login/registro; **SteamAccountCard** no perfil (vincular/desvincular/
  sincronizar biblioteca); **"Buscar da Steam"** no form de admin (autofill + navega p/ edição se
  já existir); **"Ver na Steam"** + **"Sincronizar conquistas"** no detalhe do jogo; hook
  `useSteamNotice` (toasts do `?steam=` no `Layout`).

### Verificação executada

1. **Migrações:** `makemigrations --check --dry-run` → **No changes** (nada de schema mudou).
2. **Testes:** `manage.py test` → **68/68 OK** (48 anteriores + 20 novos: callback vincula/loga/
   `nolink`/`taken`/`error` + disconnect; `steam-preview` mapeia/resolve taxonomia/`existing`/403
   p/ comum; `steam-sync` casa por appid e ignora fora do catálogo; `steam-achievements` 100%→
   platinado; guardas de `steam_id`/chave). Steam mockada — sem rede.
3. **APIs reais:** Storefront `appdetails(1145360)` (Hades) mapeou título/sinopse/imagens/
   dev/publisher/gêneros/plataformas; com a chave real, `get_schema_for_game(1145360)`→49
   conquistas, `get_owned_games` (perfil público)→1123 jogos, `get_player_achievements`→49.
4. **Frontend:** `tsc --noEmit` sem erros; `vite build` → **7194 módulos**, bundle gerado.

### Estado ao final

- Login/vínculo Steam, autofill do catálogo e sync de biblioteca/conquistas funcionais.
- O casamento de jogos é sempre por `steam_appid`; jogos possuídos fora do catálogo são
  ignorados no sync (contados na resposta) — um "importar da Steam" desses fica como evolução.

---

## Máscara do id do usuário na URL do perfil

### Objetivo

Parar de expor o id numérico sequencial do usuário na rota do perfil (`/users/1`) —
pedido de privacidade/anti-enumeração. A URL passa a mostrar o **nome** do usuário, e o id
não aparece em nenhum lugar visível do frontend.

### O que mudou (só frontend; backend intocado)

- **Novo [frontend/src/lib/profileUrl.ts](frontend/src/lib/profileUrl.ts)** — `slugifyNome`
  (remove acentos, minúsculo, hifeniza; vazio → `usuario`), `profilePath(nome)` e
  `profileLink(u)` que devolve `{ to: '/users/<slug>', state: { userId } }`.
- **Rota** `/users/:slug` (antes `:id`) em [App.tsx](frontend/src/App.tsx).
- **`ProfilePage`** lê o id de `location.state` (não mais da URL) e segue chamando
  `GET /api/profiles/:id/`. Sem id no state (link direto/refresh) → aviso "Perfil
  indisponível".
- **Os 5 pontos que montavam `/users/${id}`** passaram a usar o helper: `Navbar`,
  `ReviewCard`, `FriendsPage`, `NotificationsPage` e `EditProfilePage`.

### Decisões conscientes

| Ponto | Escolha | Motivo |
|---|---|---|
| id oculto | id trafega no `state` do router, não na URL | atende "id em lugar nenhum visível" sem mexer em schema/migração |
| Trade-off | link direto/refresh de `/users/<nome>` não carrega o perfil | fora do fluxo do app não há id resolvível; a tela mostra aviso |
| Alternativa futura | `slug` único no backend (`profiles/<slug>/`) | tornaria o link compartilhável/recarregável; exige campo `slug` + migração + backfill + trocar a busca por `slug`. Não feito. |

### Verificação executada

1. **Tipos:** `tsc --noEmit` → **sem erros**.
2. **`slugifyNome` (Node):** `"Roberto Marques"→roberto-marques`, `"João da Silva"→
   joao-da-silva`, `"Ana_Clara 99"→ana-clara-99`, `""→usuario`, `" ---"→usuario`.

### Estado ao final

- O id numérico não aparece mais na URL do perfil; a navegação interna (cliques) funciona.
- Pendente/decisão do grupo: migrar para `slug` no backend caso queiram links de perfil
  compartilháveis/recarregáveis.

---

## Frontend React (SPA completa: MVP + admin + social)

### Objetivo

Construir a SPA que consome a API DRF, conforme o plano em
[FRONTEND_TELAS.md](FRONTEND_TELAS.md) — todas as telas do MVP, o CRUD de admin em React e
as telas sociais (agora funcionais, já que os endpoints existem).

### Decisões (confirmadas antes de codar)

| Decisão | Escolha | Motivo |
|---|---|---|
| Stack | Vite + React 18 + TypeScript; react-router 6; TanStack Query; axios | SPA moderna consumindo a API por sessão/cookie |
| UI | **Mantine 7** (tema escuro), `@mantine/form`/`modals`/`notifications`/`dates` | modais/forms/inputs/notificações prontos; cores definitivas depois via tema |
| Admin | CRUD completo em React **e** Django Admin mantido | experiência unificada + rede de segurança |
| Auth de perfil | **novo `PATCH /api/auth/me/`** no backend | a `MeView` só tinha `GET`; sem isso não havia como editar o perfil |

### O que foi criado

- **Backend (item 0):** `MeView.patch` (partial update via `UserSerializer`, que já protege
  `tipo_usuario`/`steam_id` como read-only). 3 testes novos em `accounts`.
- **Frontend ([frontend/](frontend/)):** projeto Vite; `api/client.ts` (axios com
  `withCredentials` + injeção de `X-CSRFToken` + `ensureCsrf`); um módulo de API por recurso;
  `types/` espelhando os serializers; `AuthContext` (sessão, `GET /me` no boot, auto-login
  após registro) + guards `RequireAuth`/`RequireAdmin`; layout Mantine (navbar com badge de
  notificações). Páginas: login/registro, home, catálogo (busca/filtros/paginação), detalhe
  do jogo (com reviews + curtir e "adicionar à lista"), minha lista (abas por status, modal
  add/editar), perfil público (platinas em destaque, abas, botão de amizade), editar perfil,
  admin de jogos (trata **409** ao excluir jogo em listas) e de taxonomias, amigos,
  notificações, listas customizadas (CRUD + reordenar).

### Divergências/decisões conscientes

| Ponto | Escolha |
|---|---|
| Dono de uma lista na tela de detalhe | inferido comparando com `GET /api/lists/` (o serializer não expõe o `user`); controles de edição só aparecem para o dono |
| Polimorfismo do Mantine | `Group`/`Stack`/`Avatar` não tipam `component={Link}` → uso de `renderRoot` (tipado) nesses casos |
| `/settings/account` (e-mail/senha) | sem endpoint — segue só no Django Admin |
| `postcss-simple-vars` | fixado em `^7.0.1` (a `^8` não existe no npm) |

### Verificação executada

1. **Backend:** `manage.py test accounts` → **8/8 OK** (inclui os 3 do `PATCH /me`).
2. **Frontend — tipos:** `tsc --noEmit` → **sem erros**.
3. **Frontend — build:** `vite build` → **7190 módulos**, bundle gerado sem erros.
4. **Integração ao vivo (runserver + HTTP, replicando o fluxo do axios):** CSRF → login
   (Ana) → `GET /api/games/` (count=5, gêneros aninhados) → **`PATCH /api/auth/me/`** (bio
   atualizada) → `GET /api/profiles/<id>/` (`amizade=eu`, 1 platina, 3 jogos) →
   `notifications/nao-lidas` (count=2) → logout. **Todos OK.**
5. **Dev server:** `npm run dev` sobe em `:5173` e serve o `index.html` (200).

### Estado ao final

- Frontend funcional em [frontend/](frontend/) (instruções no
  [frontend/README.md](frontend/README.md)); backend com o `PATCH /me` adicionado.
- Pendente/decisão do grupo: ajuste fino de cores/tipografia do tema (deixado para depois).
- Próximos passos sugeridos: as extensões (integração Steam) sobre a base já pronta.

---

## Backend social (endpoints da extensão de rede social)

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

## Backend Django + DRF (MVP completo)

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

## Criação do banco de dados PostgreSQL

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
