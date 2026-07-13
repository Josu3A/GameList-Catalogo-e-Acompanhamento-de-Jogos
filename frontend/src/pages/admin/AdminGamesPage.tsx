import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ActionIcon,
  Badge,
  Button,
  Center,
  Group,
  Pagination,
  Stack,
  Table,
  Text,
  TextInput,
  Title,
} from '@mantine/core';
import { IconEdit, IconPlus, IconSearch, IconTrash } from '@tabler/icons-react';
import { useDebouncedValue } from '@mantine/hooks';
import { modals } from '@mantine/modals';
import { notifications } from '@mantine/notifications';
import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { deleteGame, listGames } from '../../api/games';
import { apiErrorMessage } from '../../api/client';
import type { Game } from '../../types';

const PAGE_SIZE = 20;

export function AdminGamesPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [debounced] = useDebouncedValue(search, 300);
  const [page, setPage] = useState(1);

  const { data, isLoading, isPlaceholderData } = useQuery({
    queryKey: ['admin', 'games', { debounced, page }],
    queryFn: () => listGames({ search: debounced || undefined, ordering: 'titulo', page }),
    placeholderData: keepPreviousData,
  });

  const remove = useMutation({
    mutationFn: (id: number) => deleteGame(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'games'] });
      queryClient.invalidateQueries({ queryKey: ['games'] });
      notifications.show({ color: 'green', message: 'Jogo excluído.' });
    },
    onError: (err) =>
      notifications.show({
        color: 'red',
        title: 'Não foi possível excluir',
        message: apiErrorMessage(err),
      }),
  });

  function confirmRemove(game: Game) {
    modals.openConfirmModal({
      title: 'Excluir jogo',
      children: (
        <Text size="sm">
          Excluir “{game.titulo}” do catálogo? Jogos presentes em listas de usuários não
          podem ser removidos.
        </Text>
      ),
      labels: { confirm: 'Excluir', cancel: 'Cancelar' },
      confirmProps: { color: 'red' },
      onConfirm: () => remove.mutate(game.id),
    });
  }

  const games = data?.results ?? [];
  const totalPages = data ? Math.max(1, Math.ceil(data.count / PAGE_SIZE)) : 1;

  return (
    <Stack gap="lg">
      <Group justify="space-between" wrap="wrap">
        <Title order={2}>Catálogo (admin)</Title>
        <Button component={Link} to="/admin/games/new" leftSection={<IconPlus size={16} />}>
          Novo jogo
        </Button>
      </Group>

      <TextInput
        placeholder="Buscar por título"
        leftSection={<IconSearch size={16} />}
        value={search}
        onChange={(e) => {
          setSearch(e.currentTarget.value);
          setPage(1);
        }}
        maw={320}
      />

      <Table.ScrollContainer minWidth={640}>
        <Table striped highlightOnHover style={{ opacity: isPlaceholderData ? 0.6 : 1 }}>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Título</Table.Th>
              <Table.Th>Status</Table.Th>
              <Table.Th>Ano</Table.Th>
              <Table.Th>Steam AppID</Table.Th>
              <Table.Th w={100}>Ações</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {isLoading ? (
              <Table.Tr>
                <Table.Td colSpan={5}>
                  <Text c="dimmed" ta="center" py="md">
                    Carregando…
                  </Text>
                </Table.Td>
              </Table.Tr>
            ) : games.length === 0 ? (
              <Table.Tr>
                <Table.Td colSpan={5}>
                  <Text c="dimmed" ta="center" py="md">
                    Nenhum jogo.
                  </Text>
                </Table.Td>
              </Table.Tr>
            ) : (
              games.map((g) => (
                <Table.Tr key={g.id}>
                  <Table.Td>
                    <Text component={Link} to={`/games/${g.id}`} fw={500}>
                      {g.titulo}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Badge
                      variant="light"
                      color={g.status_publicacao === 'publicado' ? 'green' : 'orange'}
                    >
                      {g.status_publicacao}
                    </Badge>
                  </Table.Td>
                  <Table.Td>{g.ano_lancamento ?? '—'}</Table.Td>
                  <Table.Td>{g.steam_appid ?? '—'}</Table.Td>
                  <Table.Td>
                    <Group gap={4} wrap="nowrap">
                      <ActionIcon
                        component={Link}
                        to={`/admin/games/${g.id}/edit`}
                        variant="subtle"
                        aria-label="Editar"
                      >
                        <IconEdit size={16} />
                      </ActionIcon>
                      <ActionIcon
                        variant="subtle"
                        color="red"
                        aria-label="Excluir"
                        onClick={() => confirmRemove(g)}
                      >
                        <IconTrash size={16} />
                      </ActionIcon>
                    </Group>
                  </Table.Td>
                </Table.Tr>
              ))
            )}
          </Table.Tbody>
        </Table>
      </Table.ScrollContainer>

      {totalPages > 1 && (
        <Center>
          <Pagination total={totalPages} value={page} onChange={setPage} />
        </Center>
      )}
    </Stack>
  );
}
