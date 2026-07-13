import { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { notifications } from '@mantine/notifications';

// Mensagens dos redirects pós-login OpenID (?steam=...) vindos do backend.
const MESSAGES: Record<string, { color: string; message: string }> = {
  login: { color: 'green', message: 'Login via Steam concluído.' },
  linked: { color: 'green', message: 'Conta Steam vinculada.' },
  nolink: {
    color: 'yellow',
    message: 'Nenhuma conta vinculada a esta Steam. Entre e vincule pelo perfil.',
  },
  taken: { color: 'red', message: 'Esta Steam já está vinculada a outra conta.' },
  error: { color: 'red', message: 'Não foi possível autenticar com a Steam.' },
};

/**
 * Lê o parâmetro `?steam=` que o backend anexa ao redirecionar de volta à SPA,
 * mostra a notificação correspondente e limpa a query da URL.
 */
export function useSteamNotice() {
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const steam = params.get('steam');
    if (!steam) return;
    const info = MESSAGES[steam];
    if (info) notifications.show(info);
    params.delete('steam');
    navigate(
      { pathname: location.pathname, search: params.toString() },
      { replace: true },
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.search]);
}
