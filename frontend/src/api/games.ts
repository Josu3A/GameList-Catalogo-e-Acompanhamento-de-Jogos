import { api, ensureCsrf } from './client';
import type { Game, NamedRef, Paginated, StatusPublicacao, SteamPreview } from '../types';

export interface GameQuery {
  search?: string;
  genero?: number;
  plataforma?: number;
  desenvolvedora?: number;
  ano?: number;
  status_publicacao?: StatusPublicacao;
  ordering?: string;
  page?: number;
}

export async function listGames(query: GameQuery = {}): Promise<Paginated<Game>> {
  const params = Object.fromEntries(
    Object.entries(query).filter(([, v]) => v !== undefined && v !== '' && v !== null),
  );
  const { data } = await api.get<Paginated<Game>>('/api/games/', { params });
  return data;
}

export async function getGame(id: number): Promise<Game> {
  const { data } = await api.get<Game>(`/api/games/${id}/`);
  return data;
}

export interface GameWritePayload {
  titulo: string;
  capa_url?: string | null;
  banner_url?: string | null;
  ano_lancamento?: number | null;
  sinopse?: string | null;
  status_publicacao: StatusPublicacao;
  steam_appid?: number | null;
  genre_ids: number[];
  platform_ids: number[];
  developer_ids: number[];
  publisher_ids: number[];
}

export async function createGame(payload: GameWritePayload): Promise<Game> {
  await ensureCsrf();
  const { data } = await api.post<Game>('/api/games/', payload);
  return data;
}

export async function updateGame(id: number, payload: Partial<GameWritePayload>): Promise<Game> {
  await ensureCsrf();
  const { data } = await api.patch<Game>(`/api/games/${id}/`, payload);
  return data;
}

/** Pode responder 409 se o jogo estiver em listas de usuários (RESTRICT). */
export async function deleteGame(id: number): Promise<void> {
  await ensureCsrf();
  await api.delete(`/api/games/${id}/`);
}

/** Autofill do catálogo pela Storefront (só admin). Resolve taxonomias e devolve IDs. */
export async function steamPreview(appid: number): Promise<SteamPreview> {
  await ensureCsrf();
  const { data } = await api.post<SteamPreview>('/api/games/steam-preview/', { appid });
  return data;
}

// --- Taxonomias (gêneros, plataformas, developers, publishers) --------------

export type Taxonomy = 'genres' | 'platforms' | 'developers' | 'publishers';

export async function listTaxonomy(kind: Taxonomy): Promise<NamedRef[]> {
  // A paginação do DRF não expõe page_size configurável aqui, então
  // percorremos as páginas seguindo `next` até esgotar (tabelas pequenas).
  const all: NamedRef[] = [];
  let page = 1;
  for (;;) {
    const { data } = await api.get<Paginated<NamedRef>>(`/api/${kind}/`, {
      params: { page },
    });
    all.push(...data.results);
    if (!data.next) break;
    page += 1;
  }
  return all;
}

export async function createTaxonomy(kind: Taxonomy, nome: string): Promise<NamedRef> {
  await ensureCsrf();
  const { data } = await api.post<NamedRef>(`/api/${kind}/`, { nome });
  return data;
}

export async function updateTaxonomy(kind: Taxonomy, id: number, nome: string): Promise<NamedRef> {
  await ensureCsrf();
  const { data } = await api.patch<NamedRef>(`/api/${kind}/${id}/`, { nome });
  return data;
}

export async function deleteTaxonomy(kind: Taxonomy, id: number): Promise<void> {
  await ensureCsrf();
  await api.delete(`/api/${kind}/${id}/`);
}
