import axios, { type InternalAxiosRequestConfig } from 'axios';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // envia/recebe os cookies de sessão e CSRF
});

function getCookie(name: string): string | null {
  const match = document.cookie.match(
    new RegExp('(^|;\\s*)' + name + '=([^;]*)'),
  );
  return match ? decodeURIComponent(match[2]) : null;
}

const UNSAFE = new Set(['post', 'put', 'patch', 'delete']);

// DRF SessionAuthentication exige X-CSRFToken em métodos não-seguros.
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const method = (config.method ?? 'get').toLowerCase();
  if (UNSAFE.has(method)) {
    const token = getCookie('csrftoken');
    if (token) {
      config.headers.set('X-CSRFToken', token);
    }
  }
  return config;
});

/** Garante o cookie csrftoken antes de qualquer mutação. */
export async function ensureCsrf(): Promise<void> {
  if (!getCookie('csrftoken')) {
    await api.get('/api/auth/csrf/');
  }
}

/** Extrai uma mensagem de erro legível de uma resposta do DRF. */
export function apiErrorMessage(err: unknown, fallback = 'Algo deu errado.'): string {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data as unknown;
    if (typeof data === 'string') return data;
    if (data && typeof data === 'object') {
      const obj = data as Record<string, unknown>;
      if (typeof obj.detail === 'string') return obj.detail;
      // Primeiro erro de validação de campo.
      for (const value of Object.values(obj)) {
        if (Array.isArray(value) && value.length && typeof value[0] === 'string') {
          return value[0];
        }
        if (typeof value === 'string') return value;
      }
    }
  }
  return fallback;
}
