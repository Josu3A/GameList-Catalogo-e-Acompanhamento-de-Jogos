import { Link } from 'react-router-dom';
import {
  Avatar,
  Button,
  Card,
  Group,
  Stack,
  Tabs,
  Text,
  Title,
} from '@mantine/core';
import { IconCheck, IconX } from '@tabler/icons-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { notifications } from '@mantine/notifications';
import {
  acceptFriendship,
  listFriendships,
  removeFriendship,
  type EstadoFiltro,
} from '../../api/social';
import { apiErrorMessage } from '../../api/client';
import { useAuth } from '../../auth/AuthContext';
import { EmptyState } from '../../components/GameCard';
import { profileLink } from '../../lib/profileUrl';
import type { Friendship, UserSummary } from '../../types';

function UserLine({ u, children }: { u: UserSummary; children?: React.ReactNode }) {
  return (
    <Card withBorder radius="md" p="sm">
      <Group justify="space-between">
        <Group
          gap="sm"
          style={{ textDecoration: 'none', color: 'inherit' }}
          renderRoot={(props) => <Link {...profileLink(u)} {...props} />}
        >
          <Avatar src={u.avatar_url ?? undefined} radius="xl">
            {u.nome.slice(0, 1).toUpperCase()}
          </Avatar>
          <Text fw={500}>{u.nome}</Text>
        </Group>
        {children}
      </Group>
    </Card>
  );
}

function FriendsTab({ estado }: { estado: EstadoFiltro }) {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['friendships', estado],
    queryFn: () => listFriendships(estado),
  });

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ['friendships'] });
    queryClient.invalidateQueries({ queryKey: ['notifications'] });
  }
  function onError(err: unknown) {
    notifications.show({ color: 'red', message: apiErrorMessage(err) });
  }

  const accept = useMutation({
    mutationFn: (id: number) => acceptFriendship(id),
    onSuccess: invalidate,
    onError,
  });
  const remove = useMutation({
    mutationFn: (id: number) => removeFriendship(id),
    onSuccess: invalidate,
    onError,
  });

  const rows = data?.results ?? [];

  // Para "amigos", o outro usuário é o que não sou eu.
  function outro(f: Friendship): UserSummary {
    return f.solicitante.id === user?.id ? f.friend : f.solicitante;
  }

  if (isLoading) return <Text c="dimmed">Carregando…</Text>;
  if (rows.length === 0) {
    const msg =
      estado === 'amigos'
        ? 'Você ainda não tem amigos.'
        : estado === 'recebidos'
          ? 'Nenhum pedido recebido.'
          : 'Nenhum pedido enviado.';
    return <EmptyState title={msg} />;
  }

  return (
    <Stack>
      {rows.map((f) => {
        if (estado === 'recebidos') {
          return (
            <UserLine key={f.id} u={f.solicitante}>
              <Group gap={6}>
                <Button
                  size="xs"
                  leftSection={<IconCheck size={14} />}
                  onClick={() => accept.mutate(f.id)}
                  loading={accept.isPending}
                >
                  Aceitar
                </Button>
                <Button
                  size="xs"
                  variant="default"
                  leftSection={<IconX size={14} />}
                  onClick={() => remove.mutate(f.id)}
                >
                  Recusar
                </Button>
              </Group>
            </UserLine>
          );
        }
        if (estado === 'enviados') {
          return (
            <UserLine key={f.id} u={f.friend}>
              <Button size="xs" variant="default" onClick={() => remove.mutate(f.id)}>
                Cancelar
              </Button>
            </UserLine>
          );
        }
        return (
          <UserLine key={f.id} u={outro(f)}>
            <Button size="xs" variant="subtle" color="red" onClick={() => remove.mutate(f.id)}>
              Desfazer
            </Button>
          </UserLine>
        );
      })}
    </Stack>
  );
}

export function FriendsPage() {
  return (
    <Stack gap="lg">
      <Title order={2}>Amigos</Title>
      <Tabs defaultValue="amigos">
        <Tabs.List mb="md">
          <Tabs.Tab value="amigos">Amigos</Tabs.Tab>
          <Tabs.Tab value="recebidos">Recebidos</Tabs.Tab>
          <Tabs.Tab value="enviados">Enviados</Tabs.Tab>
        </Tabs.List>
        <Tabs.Panel value="amigos">
          <FriendsTab estado="amigos" />
        </Tabs.Panel>
        <Tabs.Panel value="recebidos">
          <FriendsTab estado="recebidos" />
        </Tabs.Panel>
        <Tabs.Panel value="enviados">
          <FriendsTab estado="enviados" />
        </Tabs.Panel>
      </Tabs>
    </Stack>
  );
}
