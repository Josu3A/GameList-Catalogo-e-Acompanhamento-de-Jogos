import type { StatusLista, TipoNotificacao } from '../types';

export const STATUS_LISTA: Record<StatusLista, string> = {
  jogando: 'Jogando',
  completo: 'Completo',
  quero_jogar: 'Quero jogar',
  pausado: 'Pausado',
  abandonado: 'Abandonado',
};

export const STATUS_COLOR: Record<StatusLista, string> = {
  jogando: 'blue',
  completo: 'green',
  quero_jogar: 'grape',
  pausado: 'yellow',
  abandonado: 'red',
};

export const STATUS_OPTIONS = (Object.keys(STATUS_LISTA) as StatusLista[]).map(
  (value) => ({ value, label: STATUS_LISTA[value] }),
);

/** Texto de uma notificação a partir do ator e do tipo. */
export function notificationText(tipo: TipoNotificacao, actorNome?: string): string {
  const quem = actorNome ?? 'Alguém';
  switch (tipo) {
    case 'pedido_amizade':
      return `${quem} enviou um pedido de amizade.`;
    case 'amizade_aceita':
      return `${quem} aceitou seu pedido de amizade.`;
    case 'review_curtida':
      return `${quem} curtiu sua review.`;
    default:
      return 'Nova notificação.';
  }
}

/** Formata data ISO em pt-BR (só a data). */
export function formatDate(iso: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('pt-BR');
}
