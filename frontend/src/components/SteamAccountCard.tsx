import { useState } from 'react';
import { Anchor, Button, Card, Group, Stack, Text, Title } from '@mantine/core';
import { IconBrandSteam, IconRefresh, IconUnlink } from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';
import { disconnectSteam, steamLoginUrl } from '../api/auth';
import { steamSync } from '../api/library';
import { apiErrorMessage } from '../api/client';
import { useAuth } from '../auth/AuthContext';

/** Seção "Conta Steam" do perfil: vincular, desvincular e sincronizar biblioteca. */
export function SteamAccountCard() {
  const { user, refresh } = useAuth();
  const [disconnecting, setDisconnecting] = useState(false);
  const [syncing, setSyncing] = useState(false);

  if (!user) return null;

  async function handleDisconnect() {
    setDisconnecting(true);
    try {
      await disconnectSteam();
      await refresh();
      notifications.show({ color: 'green', message: 'Steam desvinculada.' });
    } catch (err) {
      notifications.show({ color: 'red', message: apiErrorMessage(err) });
    } finally {
      setDisconnecting(false);
    }
  }

  async function handleSync() {
    setSyncing(true);
    try {
      const r = await steamSync();
      notifications.show({
        color: 'green',
        message:
          `Biblioteca sincronizada: ${r.criados} novos, ${r.atualizados} atualizados` +
          `, ${r.ignorados_sem_catalogo} fora do catálogo.`,
      });
    } catch (err) {
      notifications.show({ color: 'red', message: apiErrorMessage(err) });
    } finally {
      setSyncing(false);
    }
  }

  return (
    <Card withBorder radius="md" p="lg">
      <Stack>
        <Title order={4}>Conta Steam</Title>
        {user.steam_id ? (
          <>
            <Text size="sm">
              Vinculada — SteamID{' '}
              <Anchor
                href={`https://steamcommunity.com/profiles/${user.steam_id}`}
                target="_blank"
                rel="noreferrer"
              >
                {user.steam_id}
              </Anchor>
            </Text>
            <Group>
              <Button
                leftSection={<IconRefresh size={16} />}
                onClick={handleSync}
                loading={syncing}
              >
                Sincronizar biblioteca
              </Button>
              <Button
                variant="default"
                leftSection={<IconUnlink size={16} />}
                onClick={handleDisconnect}
                loading={disconnecting}
              >
                Desvincular
              </Button>
            </Group>
            <Text size="xs" c="dimmed">
              A sincronização importa seus jogos e horas da Steam (seu perfil Steam
              precisa estar público).
            </Text>
          </>
        ) : (
          <>
            <Text size="sm" c="dimmed">
              Conecte sua conta Steam para sincronizar biblioteca e conquistas.
            </Text>
            <Button
              component="a"
              href={steamLoginUrl()}
              color="indigo"
              variant="light"
              w="fit-content"
              leftSection={<IconBrandSteam size={18} />}
            >
              Conectar Steam
            </Button>
          </>
        )}
      </Stack>
    </Card>
  );
}
