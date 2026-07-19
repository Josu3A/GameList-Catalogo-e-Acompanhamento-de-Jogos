// Tipos espelhando os serializers do backend (DRF).
// Nota: DecimalField serializa como string (nota, horas_jogadas).

export type TipoUsuario = 'comum' | 'admin';

export interface User {
  id: number;
  nome: string;
  email: string;
  tipo_usuario: TipoUsuario;
  bio: string | null;
  avatar_url: string | null;
  perfil_publico: boolean;
  steam_id: string | null;
  created_at: string;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface NamedRef {
  id: number;
  nome: string;
}

// --- Integração Steam -------------------------------------------------------

/** Retorno do autofill do catálogo (POST /api/games/steam-preview/). */
export interface SteamPreview {
  titulo: string;
  sinopse: string;
  ano_lancamento: number | null;
  /** Data precisa de lançamento (ISO), quando a RAWG casa por título. */
  data_lancamento: string | null;
  banner_url: string | null;
  capa_url: string | null;
  steam_appid: number;
  /** Id da RAWG, quando casa por título; null se não achou. */
  rawg_id: number | null;
  genres: NamedRef[];
  platforms: NamedRef[];
  developers: NamedRef[];
  publishers: NamedRef[];
  existing_game_id: number | null;
}

// --- Integração RAWG --------------------------------------------------------

/** Item do carrossel de próximos lançamentos (GET /api/games/proximos-lancamentos/). */
export interface ProximoLancamento {
  rawg_id: number;
  nome: string;
  /** Data ISO (YYYY-MM-DD). */
  data_lancamento: string;
  capa_url: string | null;
  plataformas: string[];
  /** Id do Game local, quando casado com o catálogo; null se só informativo. */
  game_id: number | null;
}

/** Resumo do sync de biblioteca (POST /api/my-games/steam-sync/). */
export interface SteamSyncResult {
  criados: number;
  atualizados: number;
  ignorados_sem_catalogo: number;
}

/** Resultado do sync de conquistas (POST /api/my-games/steam-achievements/). */
export interface SteamAchievementsResult {
  total: number;
  desbloqueadas: number;
  percent: number;
  platinado: boolean;
}

export type StatusPublicacao = 'rascunho' | 'publicado';

export interface Game {
  id: number;
  titulo: string;
  capa_url: string | null;
  banner_url: string | null;
  /** Capa vertical (biblioteca Steam) derivada do appid; usa como padrão. */
  capa_vertical_url: string | null;
  /** Fundo largo (biblioteca Steam) derivado do appid; usa como padrão. */
  banner_hero_url: string | null;
  ano_lancamento: number | null;
  /** Data precisa de lançamento (ISO), quando conhecida (RAWG ou manual). */
  data_lancamento: string | null;
  sinopse: string | null;
  status_publicacao: StatusPublicacao;
  steam_appid: number | null;
  /** Id da RAWG, usado como chave de casamento/backfill. */
  rawg_id: number | null;
  genres: NamedRef[];
  platforms: NamedRef[];
  developers: NamedRef[];
  publishers: NamedRef[];
  created_at: string;
  updated_at: string;
}

export interface GameSummary {
  id: number;
  titulo: string;
  capa_url: string | null;
  /** Capa vertical (biblioteca Steam) derivada do appid; usa como padrão. */
  capa_vertical_url: string | null;
  ano_lancamento: number | null;
}

export type StatusLista =
  | 'jogando'
  | 'completo'
  | 'quero_jogar'
  | 'pausado'
  | 'abandonado';

export interface UserGame {
  id: number;
  game: GameSummary;
  status: StatusLista;
  nota: string | null;
  horas_jogadas: string;
  platinado: boolean;
  data_inicio: string | null;
  data_fim: string | null;
  review: string | null;
  fonte: 'manual' | 'steam_sync';
  created_at: string;
  updated_at: string;
}

export interface UserGamePublic {
  id: number;
  game: GameSummary;
  status: StatusLista;
  nota: string | null;
  horas_jogadas: string;
  platinado: boolean;
  data_inicio: string | null;
  data_fim: string | null;
  review: string | null;
}

export type EstadoAmizade =
  | 'eu'
  | 'amigos'
  | 'pedido_enviado'
  | 'pedido_recebido'
  | 'nenhum'
  | null;

export interface UserSummary {
  id: number;
  nome: string;
  avatar_url: string | null;
}

/** Resultado da busca de usuários: resumo + estado da amizade com quem busca. */
export interface UserSearchResult extends UserSummary {
  amizade: EstadoAmizade;
}

export interface ListSummary {
  id: number;
  nome: string;
  descricao: string | null;
  publica: boolean;
  total_itens: number;
  created_at: string;
  updated_at: string;
}

export interface Profile {
  id: number;
  nome: string;
  bio: string | null;
  avatar_url: string | null;
  amizade: EstadoAmizade;
  platinas: UserGamePublic[];
  jogos: UserGamePublic[];
  listas_publicas: ListSummary[];
}

export type StatusAmizade = 'pendente' | 'aceito';

export interface Friendship {
  id: number;
  solicitante: UserSummary;
  friend: UserSummary;
  status: StatusAmizade;
  created_at: string;
}

export interface Review {
  id: number;
  user: UserSummary;
  game: GameSummary;
  review: string | null;
  nota: string | null;
  likes_count: number;
  liked_by_me: boolean;
  created_at: string;
}

export interface ListItem {
  game: GameSummary;
  ordem: number | null;
  added_at: string;
}

export interface ListDetail extends ListSummary {
  items: ListItem[];
}

export type TipoNotificacao =
  | 'pedido_amizade'
  | 'amizade_aceita'
  | 'review_curtida';

export type NotificationRef =
  | { friendship_id: number; status: StatusAmizade }
  | { user_game_id: number; game: string }
  | null;

export interface Notification {
  id: number;
  tipo: TipoNotificacao;
  lida: boolean;
  actor: UserSummary | null;
  referencia: NotificationRef;
  created_at: string;
}
