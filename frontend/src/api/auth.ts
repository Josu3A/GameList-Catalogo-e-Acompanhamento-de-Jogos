import { api, ensureCsrf, API_BASE_URL } from './client';
import type { User } from '../types';

export async function fetchMe(): Promise<User> {
  const { data } = await api.get<User>('/api/auth/me/');
  return data;
}

/** URL do login OpenID da Steam — usada como href (navegação de página inteira). */
export function steamLoginUrl(): string {
  return `${API_BASE_URL}/api/auth/steam/login/`;
}

/** Desvincula a Steam da conta logada; retorna o usuário atualizado. */
export async function disconnectSteam(): Promise<User> {
  await ensureCsrf();
  const { data } = await api.post<User>('/api/auth/steam/disconnect/');
  return data;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export async function login(payload: LoginPayload): Promise<User> {
  await ensureCsrf();
  const { data } = await api.post<User>('/api/auth/login/', payload);
  return data;
}

export async function logout(): Promise<void> {
  await ensureCsrf();
  await api.post('/api/auth/logout/');
}

export interface RegisterPayload {
  nome: string;
  email: string;
  password: string;
  bio?: string;
  perfil_publico?: boolean;
}

export async function register(payload: RegisterPayload): Promise<void> {
  await ensureCsrf();
  // O backend não cria sessão no registro — o AuthContext faz auto-login em seguida.
  await api.post('/api/auth/register/', payload);
}

export interface UpdateMePayload {
  nome?: string;
  email?: string;
  bio?: string | null;
  perfil_publico?: boolean;
  /** Novo arquivo de avatar (upload). Enviado como multipart. */
  avatarFile?: File | null;
  /** Se true, limpa o avatar atual (envia avatar_url = null). */
  removeAvatar?: boolean;
}

export async function updateMe(payload: UpdateMePayload): Promise<User> {
  await ensureCsrf();
  const { avatarFile, removeAvatar, ...fields } = payload;

  // Upload de novo avatar → multipart/form-data com o arquivo em avatar_url.
  if (avatarFile) {
    const form = new FormData();
    for (const [key, value] of Object.entries(fields)) {
      if (value === undefined) continue;
      // null (campo limpo, ex.: bio) vira '' para a limpeza também persistir no multipart.
      if (value === null) form.append(key, '');
      else form.append(key, typeof value === 'boolean' ? String(value) : value);
    }
    form.append('avatar_url', avatarFile);
    const { data } = await api.patch<User>('/api/auth/me/', form);
    return data;
  }

  // Sem arquivo: JSON. removeAvatar limpa o avatar (avatar_url = null).
  const body: Record<string, unknown> = { ...fields };
  if (removeAvatar) body.avatar_url = null;
  const { data } = await api.patch<User>('/api/auth/me/', body);
  return data;
}
