import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ActionIcon,
  Badge,
  Card,
  Group,
  Image,
  Menu,
  Select,
  SimpleGrid,
  Skeleton,
  Stack,
  Tabs,
  Text,
  Title,
} from '@mantine/core';
import {
  IconDeviceGamepad2,
  IconDotsVertical,
  IconEdit,
  IconStarFilled,
  IconTrash,
  IconTrophyFilled,
} from '@tabler/icons-react';
import { modals } from '@mantine/modals';
import { notifications } from '@mantine/notifications';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { deleteMyGame, listMyGames } from '../../api/library';
import { apiErrorMessage } from '../../api/client';
import { UserGameFormModal } from '../../components/UserGameFormModal';
import { StatusBadge } from '../../components/StatusBadge';
import { EmptyState } from '../../components/GameCard';
import { STATUS_LISTA } from '../../lib/labels';
import type { StatusLista, UserGame } from '../../types';

const ORDERING = [
  { value: '-updated_at', label: 'Atualizados recentemente' },
  { value: '-nota', label: 'Maior nota' },
  { value: '-horas_jogadas', label: 'Mais horas' },
];

export function MyListPage() {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<string>('todos');
  const [ordering, setOrdering] = useState('-updated_at');
  const [editing, setEditing] = useState<UserGame | null>(null);

  const status = tab === 'todos' ? undefined : (tab as StatusLista);

  const { data, isLoading } = useQuery({
    queryKey: ['my-games', { status, ordering }],
    queryFn: () => listMyGames({ status, ordering }),
  });

  const remove = useMutation({
    mutationFn: (id: number) => deleteMyGame(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-games'] });
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      notifications.show({ color: 'green', message: 'Removido da sua lista.' });
    },
    onError: (err) => notifications.show({ color: 'red', message: apiErrorMessage(err) }),
  });

  function confirmRemove(item: UserGame) {
    modals.openConfirmModal({
      title: 'Remover da lista',
      children: <Text size="sm">Remover “{item.game.titulo}” da sua lista?</Text>,
      labels: { confirm: 'Remover', cancel: 'Cancelar' },
      confirmProps: { color: 'red' },
      onConfirm: () => remove.mutate(item.id),
    });
  }

  const items = data?.results ?? [];

  return (
    <Stack gap="lg">
      <Group justify="space-between" align="flex-end" wrap="wrap">
        <Title order={2}>Minha lista</Title>
        <Select
          label="Ordenar"
          data={ORDERING}
          value={ordering}
          onChange={(v) => setOrdering(v ?? '-updated_at')}
          allowDeselect={false}
          w={220}
        />
      </Group>

      <Tabs value={tab} onChange={(v) => setTab(v ?? 'todos')}>
        <Tabs.List>
          <Tabs.Tab value="todos">Todos</Tabs.Tab>
          {(Object.keys(STATUS_LISTA) as StatusLista[]).map((s) => (
            <Tabs.Tab key={s} value={s}>
              {STATUS_LISTA[s]}
            </Tabs.Tab>
          ))}
        </Tabs.List>
      </Tabs>

      {isLoading ? (
        <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }}>
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} height={110} radius="md" />
          ))}
        </SimpleGrid>
      ) : items.length === 0 ? (
        <EmptyState
          title="Nenhum jogo aqui ainda"
          description="Navegue pelo catálogo e adicione jogos à sua lista."
        />
      ) : (
        <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }}>
          {items.map((item) => (
            <Card key={item.id} withBorder radius="md" p="sm">
              <Group wrap="nowrap" align="flex-start">
                <Link to={`/games/${item.game.id}`}>
                  {item.game.capa_url ? (
                    <Image
                      src={item.game.capa_url}
                      w={60}
                      h={80}
                      radius="sm"
                      fit="cover"
                      alt={item.game.titulo}
                    />
                  ) : (
                    <IconDeviceGamepad2 size={48} opacity={0.4} />
                  )}
                </Link>
                <Stack gap={6} style={{ flex: 1, minWidth: 0 }}>
                  <Group justify="space-between" wrap="nowrap">
                    <Text
                      fw={600}
                      size="sm"
                      lineClamp={2}
                      component={Link}
                      to={`/games/${item.game.id}`}
                      style={{ textDecoration: 'none', color: 'inherit' }}
                    >
                      {item.game.titulo}
                    </Text>
                    <Menu position="bottom-end" withinPortal>
                      <Menu.Target>
                        <ActionIcon variant="subtle" color="gray" aria-label="Ações">
                          <IconDotsVertical size={16} />
                        </ActionIcon>
                      </Menu.Target>
                      <Menu.Dropdown>
                        <Menu.Item
                          leftSection={<IconEdit size={16} />}
                          onClick={() => setEditing(item)}
                        >
                          Editar
                        </Menu.Item>
                        <Menu.Item
                          color="red"
                          leftSection={<IconTrash size={16} />}
                          onClick={() => confirmRemove(item)}
                        >
                          Remover
                        </Menu.Item>
                      </Menu.Dropdown>
                    </Menu>
                  </Group>
                  <Group gap={6}>
                    <StatusBadge status={item.status} />
                    {item.platinado && (
                      <Badge
                        color="yellow"
                        variant="light"
                        leftSection={<IconTrophyFilled size={12} />}
                      >
                        Platinado
                      </Badge>
                    )}
                  </Group>
                  <Group gap="md">
                    {item.nota !== null && (
                      <Group gap={4}>
                        <IconStarFilled size={13} color="var(--mantine-color-yellow-5)" />
                        <Text size="xs">{item.nota}</Text>
                      </Group>
                    )}
                    <Text size="xs" c="dimmed">
                      {Number(item.horas_jogadas)}h
                    </Text>
                  </Group>
                </Stack>
              </Group>
            </Card>
          ))}
        </SimpleGrid>
      )}

      <UserGameFormModal
        opened={!!editing}
        onClose={() => setEditing(null)}
        userGame={editing ?? undefined}
      />
    </Stack>
  );
}
