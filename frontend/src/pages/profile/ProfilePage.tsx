import { Link, useLocation } from 'react-router-dom';
import {
  Avatar,
  Badge,
  Button,
  Card,
  Group,
  SimpleGrid,
  Skeleton,
  Stack,
  Tabs,
  Text,
  Title,
} from '@mantine/core';
import {
  IconListDetails,
  IconTrophyFilled,
  IconUserCheck,
  IconUserPlus,
} from '@tabler/icons-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { notifications } from '@mantine/notifications';
import { getProfile } from '../../api/profiles';
import { sendFriendRequest } from '../../api/social';
import { apiErrorMessage } from '../../api/client';
import { GameCard, EmptyState } from '../../components/GameCard';
import { StatusBadge } from '../../components/StatusBadge';
import { useAuth } from '../../auth/AuthContext';
import type { UserGamePublic } from '../../types';

function GamesGrid({ jogos }: { jogos: UserGamePublic[] }) {
  if (jogos.length === 0) return <EmptyState title="Nada por aqui ainda." />;
  return (
    <SimpleGrid cols={{ base: 2, sm: 3, md: 5 }}>
      {jogos.map((ug) => (
        <GameCard
          key={ug.id}
          game={ug.game}
          badge={
            <Group gap={4}>
              <StatusBadge status={ug.status} />
              {ug.platinado && (
                <Badge color="yellow" variant="light" leftSection={<IconTrophyFilled size={11} />}>
                  Platina
                </Badge>
              )}
            </Group>
          }
        />
      ))}
    </SimpleGrid>
  );
}

export function ProfilePage() {
  // O id do usuário chega pelo `state` do router (nunca pela URL, que só mostra
  // o nome). O backend continua consultando por id em /api/profiles/{id}/.
  const location = useLocation();
  const userId = (location.state as { userId?: number } | null)?.userId ?? NaN;
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const { data: profile, isLoading, isError } = useQuery({
    queryKey: ['profile', userId],
    queryFn: () => getProfile(userId),
    enabled: Number.isFinite(userId),
    retry: false,
  });

  const addFriend = useMutation({
    mutationFn: () => sendFriendRequest(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile', userId] });
      notifications.show({ color: 'green', message: 'Pedido de amizade enviado.' });
    },
    onError: (err) => notifications.show({ color: 'red', message: apiErrorMessage(err) }),
  });

  if (!Number.isFinite(userId)) {
    return (
      <EmptyState
        title="Perfil indisponível"
        description="Abra o perfil a partir de um link dentro do app."
      />
    );
  }
  if (isLoading) return <Skeleton height={200} radius="md" />;
  if (isError || !profile) {
    return (
      <EmptyState
        title="Perfil indisponível"
        description="Este perfil não existe ou é privado."
      />
    );
  }

  function FriendAction() {
    if (!user) return null;
    switch (profile!.amizade) {
      case 'eu':
        return (
          <Button component={Link} to="/settings/profile" variant="default">
            Editar perfil
          </Button>
        );
      case 'amigos':
        return (
          <Badge size="lg" variant="light" color="green" leftSection={<IconUserCheck size={14} />}>
            Amigos
          </Badge>
        );
      case 'pedido_enviado':
        return (
          <Badge size="lg" variant="light" color="gray">
            Pedido enviado
          </Badge>
        );
      case 'pedido_recebido':
        return (
          <Button component={Link} to="/friends" variant="light">
            Responder pedido
          </Button>
        );
      case 'nenhum':
        return (
          <Button
            leftSection={<IconUserPlus size={16} />}
            onClick={() => addFriend.mutate()}
            loading={addFriend.isPending}
          >
            Adicionar amigo
          </Button>
        );
      default:
        return null;
    }
  }

  return (
    <Stack gap="lg">
      <Card withBorder radius="md" p="lg">
        <Group justify="space-between" align="flex-start" wrap="wrap">
          <Group>
            <Avatar src={profile.avatar_url ?? undefined} size={80} radius="xl">
              {profile.nome.slice(0, 1).toUpperCase()}
            </Avatar>
            <div>
              <Title order={2}>{profile.nome}</Title>
              {profile.bio && (
                <Text c="dimmed" mt={4} maw={520}>
                  {profile.bio}
                </Text>
              )}
            </div>
          </Group>
          <FriendAction />
        </Group>
      </Card>

      {profile.platinas.length > 0 && (
        <Stack gap="sm">
          <Group gap={6}>
            <IconTrophyFilled size={20} color="var(--mantine-color-yellow-5)" />
            <Title order={3}>Platinas</Title>
          </Group>
          <GamesGrid jogos={profile.platinas} />
        </Stack>
      )}

      <Tabs defaultValue="jogos">
        <Tabs.List>
          <Tabs.Tab value="jogos" leftSection={<IconListDetails size={16} />}>
            Jogos ({profile.jogos.length})
          </Tabs.Tab>
          <Tabs.Tab value="listas">Listas ({profile.listas_publicas.length})</Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="jogos" pt="md">
          <GamesGrid jogos={profile.jogos} />
        </Tabs.Panel>

        <Tabs.Panel value="listas" pt="md">
          {profile.listas_publicas.length === 0 ? (
            <EmptyState title="Nenhuma lista pública." />
          ) : (
            <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }}>
              {profile.listas_publicas.map((l) => (
                <Card
                  key={l.id}
                  withBorder
                  radius="md"
                  p="md"
                  component={Link}
                  to={`/lists/${l.id}`}
                  style={{ textDecoration: 'none', color: 'inherit' }}
                >
                  <Text fw={600}>{l.nome}</Text>
                  {l.descricao && (
                    <Text size="sm" c="dimmed" lineClamp={2}>
                      {l.descricao}
                    </Text>
                  )}
                  <Text size="xs" c="dimmed" mt="xs">
                    {l.total_itens} {l.total_itens === 1 ? 'jogo' : 'jogos'}
                  </Text>
                </Card>
              ))}
            </SimpleGrid>
          )}
        </Tabs.Panel>
      </Tabs>
    </Stack>
  );
}
