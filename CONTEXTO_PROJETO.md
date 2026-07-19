# Contexto do Projeto — GameCheck (Atividade 03 CRUD)

> Este documento resume a ideia geral do projeto e as decisões já tomadas, para dar contexto
> completo ao Claude Code antes de começar a implementação. Trata-se de uma atividade
> acadêmica de Engenharia de Software (Atividade 03 — Aplicação CRUD).

## 1. Contexto da atividade

A atividade pede a criação de uma aplicação CRUD (Create, Read, Update, Delete) em qualquer
domínio, desde que atenda a estes requisitos obrigatórios:

- Deve usar algum banco de dados relacional.
- Uma das entidades do banco deve ser o usuário.
- Deve existir **mais de um tipo de usuário** com acessos diferentes à aplicação (ex.: usuário
  comum e administrador).
- A aplicação deve ser acessada primariamente pela Web.

## 2. Ideia geral do projeto

O projeto se chama **GameCheck**: uma aplicação no estilo **MyAnimeList**,
mas para jogos, com uma pitada de rede social (parecido com Letterboxd/Backloggd no
espírito). A lógica central é:

- A plataforma mantém um **catálogo central de jogos**, curado por administradores (nome,
  capa, gênero, plataforma, ano, desenvolvedora, sinopse).
- O usuário comum **não cadastra jogos** — ele navega o catálogo já existente e "adiciona à
  sua lista pessoal", marcando um status de interação: jogando, completo, quero jogar,
  pausado, abandonado, platinado.
- Cada item da lista pessoal pode ter nota, horas jogadas e datas de início/fim.
- Componente de rede social: perfil público do usuário, destaque de jogos platinados/
  conquistas no perfil, e (extensão futura) sistema de amigos para ver listas de outras
  pessoas.

### Por que esse modelo (catálogo central + lista pessoal)?

Foi a decisão chave da conversa: em vez do usuário cadastrar jogos livremente (o que geraria
dados duplicados/inconsistentes e um requisito fraco de permissões), o catálogo é uma
entidade controlada, e **isso é o que cria naturalmente os dois tipos de usuário exigidos
pela atividade**:

- **Usuário comum**: CRUD apenas sobre a própria lista pessoal (`user_games`) — não pode
  criar, editar ou remover jogos do catálogo.
- **Administrador**: CRUD completo sobre o catálogo de jogos (`games`) — cria, edita e remove
  jogos; usuário comum só tem leitura sobre o catálogo.

## 3. Esquema de dados (preliminar)

| Tabela | Campos principais | Observações |
|---|---|---|
| `users` | id, nome, email, senha_hash, tipo_usuario (comum/admin), bio, avatar_url | Entidade de usuário exigida pela atividade; `tipo_usuario` define o nível de acesso |
| `games` | id, título, capa_url, gênero, plataforma, ano_lançamento, desenvolvedora, sinopse | Catálogo central; CRUD completo restrito ao administrador, leitura pública |
| `user_games` | id, user_id (FK), game_id (FK), status (enum), nota, horas_jogadas, platinado (bool), data_início, data_fim | Relação N:N entre `users` e `games`; é a "lista pessoal" de cada usuário |
| `friendships` (extensão futura) | id, user_id (FK), friend_id (FK), status (pendente/aceito) | Suporte ao componente de rede social |

## 4. Critérios de validação e aceitação (regras de negócio principais)

- Usuário comum não consegue criar, editar ou remover jogos do catálogo (só admin pode).
- Administrador consegue fazer CRUD completo na tabela `games`.
- Usuário comum consegue adicionar um jogo existente à sua lista e mudar o status; isso
  reflete no perfil dele.
- Um jogo marcado como "platinado" aparece destacado no perfil público do usuário.
- Um usuário não pode editar a lista de outro usuário, só visualizar (se o perfil for
  público).
- Login com credenciais inválidas é rejeitado; áreas restritas exigem autenticação.

## 5. Escopo do MVP (obrigatório) vs. extensões futuras

**MVP obrigatório** (deve funcionar de forma independente, sem depender de serviços
externos):

- CRUD de jogos (catálogo), restrito a admin.
- CRUD da lista pessoal (`user_games`), restrito ao próprio usuário.
- Autenticação com dois tipos de usuário (comum/admin).
- Perfil público com lista de jogos e destaque de platinas.

**Extensões futuras** (fora do escopo obrigatório, mas documentadas como evolução do
projeto):

1. **Sistema de amigos** — seguir outros usuários, ver perfis/listas de amigos.
2. **Integração com a Steam** (detalhada na seção 6 abaixo).
3. Integração com Epic Games/PSN/Xbox foi descartada por não existir API pública oficial
   estável para esses dados (biblioteca, conquistas) — só existem soluções não-oficiais de
   terceiros, com risco de instabilidade/banimento. Não vale o risco para este projeto.

## 6. Extensão futura — Integração com a Steam (lógica detalhada)

Essa integração foi pensada em duas frentes distintas, com propósitos e APIs diferentes:

### 6.1. Autopreenchimento do catálogo (dados da loja)

Usa a **Storefront API** da Steam (pública, sem necessidade de chave):

```
GET https://store.steampowered.com/api/appdetails?appids={appid}
```

Retorna `header_image` (banner), `short_description`/`about_the_game` (sinopse), `genres`,
`developers`, `release_date`, etc. — mapeia direto para os campos da tabela `games`.

Fluxo:
1. Admin cadastra um jogo informando apenas `steam_appid`.
2. Um job chama `appdetails` para aquele `appid`.
3. Campos `capa_url`, `sinopse`, `gênero`, `desenvolvedora`, `ano_lançamento` são preenchidos
   automaticamente.
4. Admin revisa/ajusta antes de publicar.

Referência real de projeto que faz algo parecido: o **Hydra Launcher**
(github.com/hydralauncher/hydra), que integra uma função `getGameShopDetails` ao processo de
atualização da biblioteca Steam para buscar detalhes da loja (banners, descrições) durante a
sincronização.

### 6.2. Sincronização da biblioteca do usuário

Usa a **Web API oficial** da Steam (requer chave de API e login via Steam OpenID):

| Endpoint | Uso |
|---|---|
| `ISteamUser/GetPlayerSummaries` | Dados básicos do perfil (nome, avatar) |
| `IPlayerService/GetOwnedGames` | Lista de jogos possuídos e tempo jogado (`playtime_forever`) |
| `ISteamUserStats/GetPlayerAchievements` | Conquistas desbloqueadas de um jogo |
| `ISteamUserStats/GetSchemaForGame` | Metadados das conquistas possíveis do jogo |

Fluxo:
1. Usuário clica em "Conectar Steam"; login via Steam OpenID devolve `steam_id`.
2. Job chama `GetOwnedGames` e casa cada jogo retornado com um jogo do catálogo **usando
   `steam_appid` como chave** (nunca o nome, que pode divergir).
3. Se o jogo já existe no catálogo, cria/atualiza a entrada em `user_games`, preenchendo
   `horas_jogadas`.
4. Opcionalmente busca conquistas via `GetPlayerAchievements` e calcula % de conclusão,
   sugerindo marcar como platinado.

### 6.3. Ajustes necessários no esquema para suportar isso

- `users`: adicionar `steam_id` (nullable).
- `games`: adicionar `steam_appid` (nullable).
- `user_games`: `horas_jogadas` e `platinado` passam a poder ser preenchidos
  automaticamente pela sincronização, além do preenchimento manual.

### 6.4. Pontos de atenção

- Storefront API não é oficialmente documentada, mas é estável e usada publicamente há anos
  por projetos como SteamDB, SteamSpy e o próprio Hydra Launcher.
- Web API oficial exige chave (Steam Web API Key) que deve ficar só no backend.
- Rate limit em ambas as APIs — sincronização deve ser em lote/periódica, nunca em tempo real
  a cada acesso do usuário.
- Perfil/biblioteca do usuário na Steam precisa estar público, senão a Web API não retorna
  dados.
- Casamento de jogos sempre pelo `steam_appid`, nunca pelo nome.

## 7. Tecnologias sugeridas (a confirmar com a experiência real do grupo)

- **Backend**: Python com Django (o Django Admin já oferece uma base pronta de CRUD para o
  catálogo de jogos, gerenciado pelo administrador).
- **Frontend**: templates do Django ou React consumindo API REST (Django REST Framework).
- **Banco de dados**: PostgreSQL.
- **Autenticação**: sistema nativo do Django, com dois tipos de usuário via campo de papel
  (role) ou grupos de permissão.

> Observação: essa stack é uma sugestão baseada em praticidade para o escopo acadêmico
> (Django Admin acelera bastante o CRUD do catálogo). Ajustar conforme a experiência real do
> grupo antes de começar a implementação.

## 8. O que já foi entregue

Já existe um documento formal (PDF) cobrindo a estrutura completa exigida pela atividade:
descrição da aplicação, tecnologias, esquema de dados, critérios de validação/aceitação,
plano de testes, e a seção de extensão futura com Steam. Este arquivo de contexto serve para
o Claude Code entender a ideia geral e as decisões já tomadas antes de começar a
implementação do código.
