-- ============================================================================
-- GameCheck — Schema PostgreSQL
-- ============================================================================
-- Fonte do modelo: ESQUEMA_DADOS.md / GameCheck.dbml
--
-- Uso:
--   1. Criar o banco (uma vez):   CREATE DATABASE gamelist;
--   2. Rodar este script:         psql -U postgres -d gamelist -f db/schema.sql
--   3. (Opcional) dados de demo:  psql -U postgres -d gamelist -f db/seed.sql
--
-- Convenções (ver ESQUEMA_DADOS.md §Convenções):
--   - PK surrogate BIGSERIAL, exceto junções N:N (PK composta).
--   - Enums como VARCHAR + CHECK (mais fácil de estender que ENUM nativo).
--   - created_at/updated_at TIMESTAMPTZ; updated_at mantido por trigger.
--   - Campos Steam sempre nullable (integração é opcional, não bloqueia o MVP).
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
-- Função de trigger: mantém updated_at em todo UPDATE
-- ----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 1. NÚCLEO (MVP)
-- ============================================================================

CREATE TABLE users (
  id             BIGSERIAL PRIMARY KEY,
  nome           VARCHAR(100) NOT NULL,
  email          VARCHAR(255) NOT NULL UNIQUE,
  senha_hash     VARCHAR(255) NOT NULL,  -- nunca senha em texto puro
  tipo_usuario   VARCHAR(20)  NOT NULL DEFAULT 'comum'
                 CONSTRAINT ck_users_tipo_usuario
                 CHECK (tipo_usuario IN ('comum', 'admin')),
  bio            TEXT,
  avatar_url     VARCHAR(500),
  perfil_publico BOOLEAN      NOT NULL DEFAULT true,
  steam_id       VARCHAR(20)  UNIQUE,    -- SteamID64 (extensão futura)
  created_at     TIMESTAMPTZ  NOT NULL DEFAULT now(),
  updated_at     TIMESTAMPTZ  NOT NULL DEFAULT now()
);

COMMENT ON TABLE users IS
  'Entidade de usuário. tipo_usuario define o nível de acesso (comum/admin).';

CREATE TABLE games (
  id                BIGSERIAL PRIMARY KEY,
  titulo            VARCHAR(200) NOT NULL,
  capa_url          VARCHAR(500),
  banner_url        VARCHAR(500),         -- header_image da Steam
  ano_lancamento    INTEGER,
  sinopse           TEXT,
  status_publicacao VARCHAR(20)  NOT NULL DEFAULT 'rascunho'
                    CONSTRAINT ck_games_status_publicacao
                    CHECK (status_publicacao IN ('rascunho', 'publicado')),
  steam_appid       INTEGER      UNIQUE,  -- chave de casamento com a Steam
  created_at        TIMESTAMPTZ  NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ  NOT NULL DEFAULT now()
);

COMMENT ON TABLE games IS
  'Catálogo central. CRUD restrito a admin; leitura pública.';

CREATE TABLE user_games (
  id            BIGSERIAL PRIMARY KEY,
  user_id       BIGINT       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  game_id       BIGINT       NOT NULL REFERENCES games(id) ON DELETE RESTRICT,
  status        VARCHAR(20)  NOT NULL
                CONSTRAINT ck_user_games_status
                CHECK (status IN ('jogando', 'completo', 'quero_jogar',
                                  'pausado', 'abandonado')),
  nota          DECIMAL(3,1)
                CONSTRAINT ck_user_games_nota
                CHECK (nota >= 0 AND nota <= 10),
  horas_jogadas DECIMAL(7,1) NOT NULL DEFAULT 0
                CONSTRAINT ck_user_games_horas
                CHECK (horas_jogadas >= 0),
  platinado     BOOLEAN      NOT NULL DEFAULT false,
  data_inicio   DATE,
  data_fim      DATE,
  review        TEXT,                     -- curtidas ficam em review_likes
  fonte         VARCHAR(20)  NOT NULL DEFAULT 'manual'
                CONSTRAINT ck_user_games_fonte
                CHECK (fonte IN ('manual', 'steam_sync')),
  created_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),

  CONSTRAINT uq_user_game UNIQUE (user_id, game_id)
);

COMMENT ON TABLE user_games IS
  'Lista pessoal (N:N entre users e games). status e platinado são independentes.';

-- ============================================================================
-- 2. CATÁLOGO NORMALIZADO (N:N)
-- ============================================================================

CREATE TABLE genres (
  id   BIGSERIAL PRIMARY KEY,
  nome VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE platforms (
  id   BIGSERIAL PRIMARY KEY,
  nome VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE developers (
  id   BIGSERIAL PRIMARY KEY,
  nome VARCHAR(150) NOT NULL UNIQUE
);

CREATE TABLE publishers (
  id   BIGSERIAL PRIMARY KEY,
  nome VARCHAR(150) NOT NULL UNIQUE
);

CREATE TABLE game_genres (
  game_id  BIGINT NOT NULL REFERENCES games(id)  ON DELETE CASCADE,
  genre_id BIGINT NOT NULL REFERENCES genres(id) ON DELETE CASCADE,
  PRIMARY KEY (game_id, genre_id)
);

CREATE TABLE game_platforms (
  game_id     BIGINT NOT NULL REFERENCES games(id)     ON DELETE CASCADE,
  platform_id BIGINT NOT NULL REFERENCES platforms(id) ON DELETE CASCADE,
  PRIMARY KEY (game_id, platform_id)
);

CREATE TABLE game_developers (
  game_id      BIGINT NOT NULL REFERENCES games(id)      ON DELETE CASCADE,
  developer_id BIGINT NOT NULL REFERENCES developers(id) ON DELETE CASCADE,
  PRIMARY KEY (game_id, developer_id)
);

CREATE TABLE game_publishers (
  game_id      BIGINT NOT NULL REFERENCES games(id)      ON DELETE CASCADE,
  publisher_id BIGINT NOT NULL REFERENCES publishers(id) ON DELETE CASCADE,
  PRIMARY KEY (game_id, publisher_id)
);

-- ============================================================================
-- 3. INTEGRAÇÃO STEAM (extensão futura)
-- ============================================================================

CREATE TABLE achievements (
  id            BIGSERIAL PRIMARY KEY,
  game_id       BIGINT       NOT NULL REFERENCES games(id) ON DELETE CASCADE,
  steam_apiname VARCHAR(200) NOT NULL,  -- nome interno da conquista na Steam
  nome          VARCHAR(200) NOT NULL,
  descricao     TEXT,
  icon_url      VARCHAR(500),

  CONSTRAINT uq_game_achievement UNIQUE (game_id, steam_apiname)
);

COMMENT ON TABLE achievements IS
  'Esquema de conquistas de um jogo (GetSchemaForGame).';

CREATE TABLE user_achievements (
  id              BIGSERIAL PRIMARY KEY,
  user_id         BIGINT NOT NULL REFERENCES users(id)        ON DELETE CASCADE,
  achievement_id  BIGINT NOT NULL REFERENCES achievements(id) ON DELETE CASCADE,
  desbloqueada_em TIMESTAMPTZ,

  CONSTRAINT uq_user_achievement UNIQUE (user_id, achievement_id)
);

COMMENT ON TABLE user_achievements IS
  'Conquistas desbloqueadas por um usuário (GetPlayerAchievements).';

-- ============================================================================
-- 4. REDE SOCIAL E ORGANIZAÇÃO (extensões)
-- ============================================================================

CREATE TABLE friendships (
  id         BIGSERIAL PRIMARY KEY,
  user_id    BIGINT      NOT NULL REFERENCES users(id) ON DELETE CASCADE,  -- quem solicitou
  friend_id  BIGINT      NOT NULL REFERENCES users(id) ON DELETE CASCADE,  -- quem recebeu
  status     VARCHAR(20) NOT NULL DEFAULT 'pendente'
             CONSTRAINT ck_friendships_status
             CHECK (status IN ('pendente', 'aceito')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT uq_friendship UNIQUE (user_id, friend_id),
  CONSTRAINT ck_friendship_nao_reflexiva CHECK (user_id <> friend_id)
);

COMMENT ON TABLE friendships IS
  'Auto-relacionamento em users. user_id solicitou; friend_id recebeu.';

CREATE TABLE review_likes (
  user_game_id BIGINT      NOT NULL REFERENCES user_games(id) ON DELETE CASCADE,  -- a review curtida
  user_id      BIGINT      NOT NULL REFERENCES users(id)      ON DELETE CASCADE,  -- quem curtiu
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (user_game_id, user_id)
);

COMMENT ON TABLE review_likes IS
  'Curtidas em reviews (N:N). A review é a linha de user_games com review não-nulo.';

CREATE TABLE lists (
  id         BIGSERIAL PRIMARY KEY,
  user_id    BIGINT       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  nome       VARCHAR(150) NOT NULL,
  descricao  TEXT,
  publica    BOOLEAN      NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ  NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ  NOT NULL DEFAULT now(),

  CONSTRAINT uq_list_user_nome UNIQUE (user_id, nome)
);

COMMENT ON TABLE lists IS
  'Listas/coleções customizadas do usuário (ex.: "Top 10 RPGs").';

CREATE TABLE list_items (
  list_id  BIGINT      NOT NULL REFERENCES lists(id) ON DELETE CASCADE,
  game_id  BIGINT      NOT NULL REFERENCES games(id) ON DELETE RESTRICT,
  ordem    INTEGER,                       -- posição opcional na lista
  added_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (list_id, game_id)
);

COMMENT ON TABLE list_items IS
  'Jogos dentro de uma lista customizada (N:N entre lists e games).';

CREATE TABLE notifications (
  id            BIGSERIAL PRIMARY KEY,
  user_id       BIGINT      NOT NULL REFERENCES users(id) ON DELETE CASCADE,   -- destinatário
  actor_id      BIGINT      REFERENCES users(id) ON DELETE SET NULL,           -- quem gerou o evento
  tipo          VARCHAR(20) NOT NULL
                CONSTRAINT ck_notifications_tipo
                CHECK (tipo IN ('pedido_amizade', 'amizade_aceita', 'review_curtida')),
  friendship_id BIGINT      REFERENCES friendships(id) ON DELETE CASCADE,
  user_game_id  BIGINT      REFERENCES user_games(id)  ON DELETE CASCADE,
  lida          BOOLEAN     NOT NULL DEFAULT false,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),

  -- Exatamente uma referência preenchida, conforme o tipo (ESQUEMA_DADOS §4.4)
  CONSTRAINT ck_notifications_referencia CHECK (
    (tipo IN ('pedido_amizade', 'amizade_aceita')
       AND friendship_id IS NOT NULL AND user_game_id IS NULL)
    OR
    (tipo = 'review_curtida'
       AND user_game_id IS NOT NULL AND friendship_id IS NULL)
  )
);

COMMENT ON TABLE notifications IS
  'Notificações do usuário. FKs separadas + CHECK garantem exatamente uma referência.';

-- ============================================================================
-- 5. ÍNDICES ADICIONAIS (além dos criados por PK/UNIQUE — ESQUEMA_DADOS §5)
-- ============================================================================

CREATE INDEX idx_user_games_user ON user_games (user_id);
CREATE INDEX idx_user_games_game ON user_games (game_id);

-- Destaque de platinas no perfil (índice parcial)
CREATE INDEX idx_user_games_platinados ON user_games (user_id) WHERE platinado = true;

CREATE INDEX idx_friendships_friend ON friendships (friend_id);
CREATE INDEX idx_review_likes_user  ON review_likes (user_id);
CREATE INDEX idx_notifications_user_lida ON notifications (user_id, lida);

-- ============================================================================
-- 6. TRIGGERS DE updated_at
-- ============================================================================

CREATE TRIGGER trg_users_updated_at
  BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_games_updated_at
  BEFORE UPDATE ON games
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_user_games_updated_at
  BEFORE UPDATE ON user_games
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_lists_updated_at
  BEFORE UPDATE ON lists
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

COMMIT;
