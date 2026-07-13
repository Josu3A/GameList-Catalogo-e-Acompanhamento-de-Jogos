import { api, ensureCsrf } from './client';
import type {
  Paginated,
  StatusLista,
  SteamAchievementsResult,
  SteamSyncResult,
  UserGame,
} from '../types';

export interface MyGamesQuery {
  status?: StatusLista;
  platinado?: boolean;
  ordering?: string;
  page?: number;
}

export async function listMyGames(query: MyGamesQuery = {}): Promise<Paginated<UserGame>> {
  const params = Object.fromEntries(
    Object.entries(query).filter(([, v]) => v !== undefined && v !== '' && v !== null),
  );
  const { data } = await api.get<Paginated<UserGame>>('/api/my-games/', { params });
  return data;
}

export interface UserGameWritePayload {
  game_id: number;
  status: StatusLista;
  nota?: number | null;
  horas_jogadas?: number;
  platinado?: boolean;
  data_inicio?: string | null;
  data_fim?: string | null;
  review?: string | null;
}

export async function addMyGame(payload: UserGameWritePayload): Promise<UserGame> {
  await ensureCsrf();
  const { data } = await api.post<UserGame>('/api/my-games/', payload);
  return data;
}

export async function updateMyGame(
  id: number,
  payload: Partial<Omit<UserGameWritePayload, 'game_id'>>,
): Promise<UserGame> {
  await ensureCsrf();
  const { data } = await api.patch<UserGame>(`/api/my-games/${id}/`, payload);
  return data;
}

export async function deleteMyGame(id: number): Promise<void> {
  await ensureCsrf();
  await api.delete(`/api/my-games/${id}/`);
}

// --- Integração Steam -------------------------------------------------------

/** Importa jogos possuídos + horas para a lista pessoal (fonte steam_sync). */
export async function steamSync(): Promise<SteamSyncResult> {
  await ensureCsrf();
  const { data } = await api.post<SteamSyncResult>('/api/my-games/steam-sync/');
  return data;
}

/** Sincroniza as conquistas de um jogo da lista; sugere platinado a 100%. */
export async function steamAchievements(gameId: number): Promise<SteamAchievementsResult> {
  await ensureCsrf();
  const { data } = await api.post<SteamAchievementsResult>(
    '/api/my-games/steam-achievements/',
    { game_id: gameId },
  );
  return data;
}
