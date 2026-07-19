import { api, ensureCsrf } from './client';
import type {
  Friendship,
  ListDetail,
  ListSummary,
  Notification,
  Paginated,
  Review,
  UserSearchResult,
} from '../types';

// --- Amigos -----------------------------------------------------------------

export type EstadoFiltro = 'amigos' | 'recebidos' | 'enviados';

export async function listFriendships(estado: EstadoFiltro): Promise<Paginated<Friendship>> {
  const { data } = await api.get<Paginated<Friendship>>('/api/friendships/', {
    params: { estado },
  });
  return data;
}

export async function searchUsers(q: string): Promise<Paginated<UserSearchResult>> {
  const { data } = await api.get<Paginated<UserSearchResult>>('/api/users/search/', {
    params: { q },
  });
  return data;
}

export async function sendFriendRequest(friendId: number): Promise<Friendship> {
  await ensureCsrf();
  const { data } = await api.post<Friendship>('/api/friendships/', { friend_id: friendId });
  return data;
}

export async function acceptFriendship(id: number): Promise<Friendship> {
  await ensureCsrf();
  const { data } = await api.post<Friendship>(`/api/friendships/${id}/aceitar/`);
  return data;
}

export async function removeFriendship(id: number): Promise<void> {
  await ensureCsrf();
  await api.delete(`/api/friendships/${id}/`);
}

// --- Reviews + curtidas -----------------------------------------------------

export async function listReviews(gameId?: number): Promise<Paginated<Review>> {
  const { data } = await api.get<Paginated<Review>>('/api/reviews/', {
    params: gameId ? { game: gameId } : {},
  });
  return data;
}

export async function likeReview(userGameId: number): Promise<Review> {
  await ensureCsrf();
  const { data } = await api.post<Review>(`/api/reviews/${userGameId}/like/`);
  return data;
}

export async function unlikeReview(userGameId: number): Promise<Review> {
  await ensureCsrf();
  const { data } = await api.delete<Review>(`/api/reviews/${userGameId}/like/`);
  return data;
}

// --- Listas customizadas ----------------------------------------------------

export async function listMyLists(): Promise<Paginated<ListSummary>> {
  const { data } = await api.get<Paginated<ListSummary>>('/api/lists/');
  return data;
}

export async function listUserLists(userId: number): Promise<Paginated<ListSummary>> {
  const { data } = await api.get<Paginated<ListSummary>>('/api/lists/', {
    params: { user: userId },
  });
  return data;
}

export async function getList(id: number): Promise<ListDetail> {
  const { data } = await api.get<ListDetail>(`/api/lists/${id}/`);
  return data;
}

export interface ListWritePayload {
  nome: string;
  descricao?: string | null;
  publica?: boolean;
}

export async function createList(payload: ListWritePayload): Promise<ListDetail> {
  await ensureCsrf();
  const { data } = await api.post<ListDetail>('/api/lists/', payload);
  return data;
}

export async function updateList(id: number, payload: Partial<ListWritePayload>): Promise<ListDetail> {
  await ensureCsrf();
  const { data } = await api.patch<ListDetail>(`/api/lists/${id}/`, payload);
  return data;
}

export async function deleteList(id: number): Promise<void> {
  await ensureCsrf();
  await api.delete(`/api/lists/${id}/`);
}

export async function addListItem(listId: number, gameId: number, ordem?: number): Promise<void> {
  await ensureCsrf();
  await api.post(`/api/lists/${listId}/items/`, { game_id: gameId, ordem });
}

export async function removeListItem(listId: number, gameId: number): Promise<void> {
  await ensureCsrf();
  await api.delete(`/api/lists/${listId}/items/${gameId}/`);
}

export async function reorderList(listId: number, gameIds: number[]): Promise<ListDetail> {
  await ensureCsrf();
  const { data } = await api.patch<ListDetail>(`/api/lists/${listId}/reorder/`, {
    game_ids: gameIds,
  });
  return data;
}

// --- Notificações -----------------------------------------------------------

export async function listNotifications(): Promise<Paginated<Notification>> {
  const { data } = await api.get<Paginated<Notification>>('/api/notifications/');
  return data;
}

export async function unreadCount(): Promise<number> {
  const { data } = await api.get<{ count: number }>('/api/notifications/nao-lidas/');
  return data.count;
}

export async function markNotificationRead(id: number): Promise<void> {
  await ensureCsrf();
  await api.post(`/api/notifications/${id}/marcar-lida/`);
}

export async function markAllNotificationsRead(): Promise<void> {
  await ensureCsrf();
  await api.post('/api/notifications/marcar-todas-lidas/');
}
