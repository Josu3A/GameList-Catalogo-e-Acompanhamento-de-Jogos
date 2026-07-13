import { Button } from '@mantine/core';
import { IconBrandSteam } from '@tabler/icons-react';
import { steamLoginUrl } from '../api/auth';

/**
 * Botão de login por Steam. É um link de página inteira (o OpenID exige
 * redirecionamento do navegador, não uma chamada XHR). Só loga contas que já
 * vincularam a Steam; SteamID desconhecido volta ao login com aviso.
 */
export function SteamLoginButton({ label = 'Entrar com Steam' }: { label?: string }) {
  return (
    <Button
      component="a"
      href={steamLoginUrl()}
      color="indigo"
      variant="light"
      fullWidth
      leftSection={<IconBrandSteam size={18} />}
    >
      {label}
    </Button>
  );
}
