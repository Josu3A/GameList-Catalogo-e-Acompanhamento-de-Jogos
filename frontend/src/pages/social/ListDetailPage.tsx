import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import {
  ActionIcon,
  Badge,
  Button,
  Card,
  Group,
  Image,
  Select,
  Skeleton,
  Stack,
  Text,
  Title,
} from '@mantine/core';
import {
  IconArrowDown,
  IconArrowUp,
  IconDeviceGamepad2,
  IconTrash,
} from '@tabler/icons-react';
import { useDebouncedValue } from '@mantine/hooks';
import { modals } from '@mantine/modals';
import { notifications } from '@mantine/notifications';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  addListItem,
  deleteList,
  getList,
  listMyLists,
  removeListItem,
  reorderList,
} from '../../api/social';
import { listGames } from '../../api/games';
import { apiErrorMessage } from '../../api/client';
import { useAuth } from '../../auth/AuthContext';
import { EmptyState } from '../../components/GameCard';

function AddGame({ listId }: { listId: number }) {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [debounced] = useDebouncedValue(search, 300);

  const games = useQuery({
    queryKey: ['games', 'list-picker', debounced],
    queryFn: () => listGames({ search: debounced || undefined, ordering: 'titulo' }),
  });

  const add = useMutation({
    mutationFn: (gameId: number) => addListItem(listId, gameId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['list', listId] });
      setSearch('');
      notifications.show({ color: 'green', message: 'Jogo adicionado à lista.' });
    },
    onError: (err) => notifications.show({ color: 'red', message: apiErrorMessage(err) }),
  });

  return (
    <Select
      label="Adicionar jogo"
      placeholder="Buscar no catálogo…"
      searchable
      searchValue={search}
      onSearchChange={setSearch}
      nothingFoundMessage={debounced ? 'Nenhum jogo' : 'Digite para buscar'}
      data={(games.data?.results ?? []).map((g) => ({
        value: String(g.id),
        label: g.titulo,
      }))}
      value={null}
      onChange={(v) => v && add.mutate(Number(v))}
      maw={360}
    />
  );
}

export function ListDetailPage() {
  const { id } = useParams();
  const listId = Number(id);
  const { user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: list, isLoading, isError } = useQuery({
    queryKey: ['list', listId],
    queryFn: () => getList(listId),
    enabled: Number.isFinite(listId),
    retry: false,
  });

  // Descobrir se o usuário atual é dono (o serializer não expõe o owner).
  const myLists = useQuery({
    queryKey: ['lists', 'mine'],
    queryFn: listMyLists,
    enabled: !!user,
  });
  const isOwner = !!myLists.data?.results.some((l) => l.id === listId);

  // Ordem local dos game_ids (para reordenar antes de persistir).
  const [order, setOrder] = useState<number[]>([]);
  useEffect(() => {
    if (list) setOrder(list.items.map((it) => it.game.id));
  }, [list]);

  const reorder = useMutation({
    mutationFn: (gameIds: number[]) => reorderList(listId, gameIds),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['list', listId] }),
    onError: (err) => notifications.show({ color: 'red', message: apiErrorMessage(err) }),
  });

  const removeItem = useMutation({
    mutationFn: (gameId: number) => removeListItem(listId, gameId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['list', listId] }),
    onError: (err) => notifications.show({ color: 'red', message: apiErrorMessage(err) }),
  });

  const removeList = useMutation({
    mutationFn: () => deleteList(listId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lists'] });
      notifications.show({ color: 'green', message: 'Lista excluída.' });
      navigate('/lists');
    },
    onError: (err) => notifications.show({ color: 'red', message: apiErrorMessage(err) }),
  });

  function move(index: number, dir: -1 | 1) {
    const target = index + dir;
    if (target < 0 || target >= order.length) return;
    const next = [...order];
    [next[index], next[target]] = [next[target], next[index]];
    setOrder(next);
    reorder.mutate(next);
  }

  function confirmDeleteList() {
    modals.openConfirmModal({
      title: 'Excluir lista',
      children: <Text size="sm">Excluir a lista “{list?.nome}”?</Text>,
      labels: { confirm: 'Excluir', cancel: 'Cancelar' },
      confirmProps: { color: 'red' },
      onConfirm: () => removeList.mutate(),
    });
  }

  if (isLoading) return <Skeleton height={200} radius="md" />;
  if (isError || !list) {
    return <EmptyState title="Lista indisponível" description="Ela não existe ou é privada." />;
  }

  // Renderiza na ordem local (mantém consistência durante o reorder).
  const itemsByGame = new Map(list.items.map((it) => [it.game.id, it]));
  const ordered = order
    .map((gid) => itemsByGame.get(gid))
    .filter((x): x is NonNullable<typeof x> => !!x);

  return (
    <Stack gap="lg">
      <Group justify="space-between" align="flex-start" wrap="wrap">
        <div>
          <Group gap={8}>
            <Title order={2}>{list.nome}</Title>
            {!list.publica && (
              <Badge variant="light" color="gray">
                privada
              </Badge>
            )}
          </Group>
          {list.descricao && (
            <Text c="dimmed" mt={4}>
              {list.descricao}
            </Text>
          )}
        </div>
        {isOwner && (
          <Button variant="subtle" color="red" onClick={confirmDeleteList}>
            Excluir lista
          </Button>
        )}
      </Group>

      {isOwner && <AddGame listId={listId} />}

      {ordered.length === 0 ? (
        <EmptyState title="Lista vazia" description={isOwner ? 'Adicione jogos acima.' : undefined} />
      ) : (
        <Stack gap="xs">
          {ordered.map((it, index) => (
            <Card key={it.game.id} withBorder radius="md" p="sm">
              <Group justify="space-between" wrap="nowrap">
                <Group wrap="nowrap" style={{ minWidth: 0 }}>
                  <Text c="dimmed" w={24} ta="right">
                    {index + 1}
                  </Text>
                  <Link to={`/games/${it.game.id}`}>
                    {it.game.capa_url ? (
                      <Image src={it.game.capa_url} w={40} h={54} radius="sm" fit="cover" alt="" />
                    ) : (
                      <IconDeviceGamepad2 size={36} opacity={0.4} />
                    )}
                  </Link>
                  <Text
                    fw={500}
                    lineClamp={1}
                    component={Link}
                    to={`/games/${it.game.id}`}
                    style={{ textDecoration: 'none', color: 'inherit' }}
                  >
                    {it.game.titulo}
                  </Text>
                </Group>
                {isOwner && (
                  <Group gap={4} wrap="nowrap">
                    <ActionIcon
                      variant="subtle"
                      disabled={index === 0 || reorder.isPending}
                      onClick={() => move(index, -1)}
                      aria-label="Mover para cima"
                    >
                      <IconArrowUp size={16} />
                    </ActionIcon>
                    <ActionIcon
                      variant="subtle"
                      disabled={index === ordered.length - 1 || reorder.isPending}
                      onClick={() => move(index, 1)}
                      aria-label="Mover para baixo"
                    >
                      <IconArrowDown size={16} />
                    </ActionIcon>
                    <ActionIcon
                      variant="subtle"
                      color="red"
                      onClick={() => removeItem.mutate(it.game.id)}
                      aria-label="Remover"
                    >
                      <IconTrash size={16} />
                    </ActionIcon>
                  </Group>
                )}
              </Group>
            </Card>
          ))}
        </Stack>
      )}
    </Stack>
  );
}
