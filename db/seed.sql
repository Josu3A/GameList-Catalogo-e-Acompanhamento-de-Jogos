-- ============================================================================
-- GameCheck — Seed (dados de demonstração)
-- ============================================================================
-- Rodar DEPOIS de db/schema.sql, em banco recém-criado:
--   psql -U postgres -d gamelist -f db/seed.sql
--
-- ATENÇÃO: os valores de senha_hash abaixo são PLACEHOLDERS ilustrativos.
-- A aplicação deve gerar hashes reais (bcrypt/argon2) no cadastro; estes
-- usuários de demo não devem permitir login em produção.
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
-- Usuários: 1 admin + 2 comuns
-- ----------------------------------------------------------------------------

INSERT INTO users (id, nome, email, senha_hash, tipo_usuario, bio, perfil_publico) VALUES
  (1, 'Administrador', 'admin@gamelist.dev',
   '$2b$12$PLACEHOLDER.hash.admin.trocar.na.aplicacao000000000000',
   'admin', 'Curador do catálogo.', true),
  (2, 'Ana Souza', 'ana@gamelist.dev',
   '$2b$12$PLACEHOLDER.hash.ana.trocar.na.aplicacao00000000000000',
   'comum', 'Caçadora de platinas e fã de indies.', true),
  (3, 'Bruno Lima', 'bruno@gamelist.dev',
   '$2b$12$PLACEHOLDER.hash.bruno.trocar.na.aplicacao000000000000',
   'comum', 'Backlog eterno, mas um dia eu zero tudo.', true);

SELECT setval(pg_get_serial_sequence('users', 'id'), (SELECT max(id) FROM users));

-- ----------------------------------------------------------------------------
-- Catálogo de referência: gêneros, plataformas, developers, publishers
-- ----------------------------------------------------------------------------

INSERT INTO genres (id, nome) VALUES
  (1, 'Ação'),
  (2, 'RPG'),
  (3, 'Aventura'),
  (4, 'Indie'),
  (5, 'Simulação'),
  (6, 'Roguelike'),
  (7, 'Plataforma'),
  (8, 'Metroidvania');

SELECT setval(pg_get_serial_sequence('genres', 'id'), (SELECT max(id) FROM genres));

INSERT INTO platforms (id, nome) VALUES
  (1, 'PC'),
  (2, 'PlayStation 5'),
  (3, 'PlayStation 4'),
  (4, 'Xbox Series X|S'),
  (5, 'Xbox One'),
  (6, 'Nintendo Switch');

SELECT setval(pg_get_serial_sequence('platforms', 'id'), (SELECT max(id) FROM platforms));

INSERT INTO developers (id, nome) VALUES
  (1, 'FromSoftware'),
  (2, 'Supergiant Games'),
  (3, 'ConcernedApe'),
  (4, 'Team Cherry'),
  (5, 'Extremely OK Games');

SELECT setval(pg_get_serial_sequence('developers', 'id'), (SELECT max(id) FROM developers));

INSERT INTO publishers (id, nome) VALUES
  (1, 'Bandai Namco Entertainment'),
  (2, 'Supergiant Games'),
  (3, 'ConcernedApe'),
  (4, 'Team Cherry'),
  (5, 'Extremely OK Games');

SELECT setval(pg_get_serial_sequence('publishers', 'id'), (SELECT max(id) FROM publishers));

-- ----------------------------------------------------------------------------
-- Jogos (steam_appid reais — chave de casamento com a Steam)
-- ----------------------------------------------------------------------------

INSERT INTO games (id, titulo, ano_lancamento, sinopse, status_publicacao, steam_appid) VALUES
  (1, 'Elden Ring', 2022,
   'RPG de ação em mundo aberto nas Terras Intermédias, criado por Hidetaka Miyazaki e George R. R. Martin.',
   'publicado', 1245620),
  (2, 'Hades', 2020,
   'Roguelike de ação em que Zagreus tenta escapar do submundo grego, desafiando o próprio pai, Hades.',
   'publicado', 1145360),
  (3, 'Stardew Valley', 2016,
   'Simulador de fazenda: herde um terreno, cultive, crie animais e faça parte da comunidade de Vale do Orvalho.',
   'publicado', 413150),
  (4, 'Hollow Knight', 2017,
   'Metroidvania sombrio no reino subterrâneo de Hallownest, habitado por insetos e segredos.',
   'publicado', 367520),
  (5, 'Celeste', 2018,
   'Plataforma de precisão: ajude Madeline a escalar a montanha Celeste e enfrentar seus próprios demônios.',
   'publicado', 504230);

SELECT setval(pg_get_serial_sequence('games', 'id'), (SELECT max(id) FROM games));

-- Junções do catálogo -------------------------------------------------------

INSERT INTO game_genres (game_id, genre_id) VALUES
  (1, 1), (1, 2),          -- Elden Ring: Ação, RPG
  (2, 1), (2, 4), (2, 6),  -- Hades: Ação, Indie, Roguelike
  (3, 4), (3, 5),          -- Stardew Valley: Indie, Simulação
  (4, 3), (4, 4), (4, 8),  -- Hollow Knight: Aventura, Indie, Metroidvania
  (5, 4), (5, 7);          -- Celeste: Indie, Plataforma

INSERT INTO game_platforms (game_id, platform_id) VALUES
  (1, 1), (1, 2), (1, 3), (1, 4), (1, 5),  -- Elden Ring
  (2, 1), (2, 2), (2, 4), (2, 6),          -- Hades
  (3, 1), (3, 3), (3, 5), (3, 6),          -- Stardew Valley
  (4, 1), (4, 3), (4, 5), (4, 6),          -- Hollow Knight
  (5, 1), (5, 3), (5, 5), (5, 6);          -- Celeste

INSERT INTO game_developers (game_id, developer_id) VALUES
  (1, 1),  -- Elden Ring ← FromSoftware
  (2, 2),  -- Hades ← Supergiant Games
  (3, 3),  -- Stardew Valley ← ConcernedApe
  (4, 4),  -- Hollow Knight ← Team Cherry
  (5, 5);  -- Celeste ← Extremely OK Games

INSERT INTO game_publishers (game_id, publisher_id) VALUES
  (1, 1),  -- Elden Ring ← Bandai Namco
  (2, 2),  -- Hades ← Supergiant Games
  (3, 3),  -- Stardew Valley ← ConcernedApe
  (4, 4),  -- Hollow Knight ← Team Cherry
  (5, 5);  -- Celeste ← Extremely OK Games

-- ----------------------------------------------------------------------------
-- Listas pessoais (user_games) — cobre todos os status dos critérios de aceitação
-- ----------------------------------------------------------------------------

INSERT INTO user_games
  (id, user_id, game_id, status, nota, horas_jogadas, platinado,
   data_inicio, data_fim, review, fonte) VALUES
  -- Ana (user 2): platina em Hades + review (destaque de platina no perfil)
  (1, 2, 2, 'completo', 9.5, 112.0, true,
   '2026-01-10', '2026-03-02',
   'Roguelike perfeito: cada tentativa avança a história. A platina é trabalhosa mas justa.',
   'manual'),
  (2, 2, 4, 'jogando', NULL, 21.5, false,
   '2026-06-01', NULL, NULL, 'manual'),
  (3, 2, 1, 'quero_jogar', NULL, 0, false,
   NULL, NULL, NULL, 'manual'),

  -- Bruno (user 3): status variados; Stardew veio da sincronização Steam
  (4, 3, 3, 'pausado', 8.0, 64.3, false,
   '2025-11-20', NULL, NULL, 'steam_sync'),
  (5, 3, 5, 'abandonado', 6.5, 4.2, false,
   '2026-02-05', NULL,
   'Jogo lindo, mas meus dedos não acompanham o capítulo 5.', 'manual'),
  (6, 3, 1, 'completo', 10.0, 98.0, false,
   '2026-03-10', '2026-05-28', NULL, 'manual');

SELECT setval(pg_get_serial_sequence('user_games', 'id'), (SELECT max(id) FROM user_games));

-- ----------------------------------------------------------------------------
-- Rede social (demonstração das extensões)
-- ----------------------------------------------------------------------------

-- Bruno curtiu a review da Ana sobre Hades
INSERT INTO review_likes (user_game_id, user_id) VALUES (1, 3);

-- Amizade aceita entre Ana e Bruno
INSERT INTO friendships (id, user_id, friend_id, status) VALUES
  (1, 2, 3, 'aceito');

SELECT setval(pg_get_serial_sequence('friendships', 'id'), (SELECT max(id) FROM friendships));

-- Notificações correspondentes (respeitam o CHECK de referência exatamente-uma)
INSERT INTO notifications (user_id, actor_id, tipo, friendship_id, user_game_id, lida) VALUES
  (3, 2, 'pedido_amizade', 1, NULL, true),   -- Bruno recebeu o pedido da Ana
  (2, 3, 'amizade_aceita', 1, NULL, false),  -- Ana foi notificada do aceite
  (2, 3, 'review_curtida', NULL, 1, false);  -- Ana foi notificada da curtida do Bruno

COMMIT;
