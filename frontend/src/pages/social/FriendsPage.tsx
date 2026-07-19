import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Avatar,
  Badge,
  Button,
  Card,
  Group,
  Modal,
  Stack,
  Tabs,
  Text,
  TextInput,
  Title,
} from '@mantine/core';
import { useDebouncedValue, useDisclosure } from '@mantine/hooks';
import {
  IconCheck,
  IconSearch,
  IconUserCheck,
  IconUserPlus,
  IconX,
} from '@tabler/icons-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { notifications } from '@mantine/notifications';
import {
  acceptFriendship,
  listFriendships,
  removeFriendship,
  searchUsers,
  sendFriendRequest,
  type EstadoFiltro,
} from '../../api/social';
import { apiErrorMessage } from '../../api/client';
import { useAuth } from '../../auth/AuthContext';
import { EmptyState } from '../../components/GameCard';
import { profileLink } from '../../lib/profileUrl';
import type { Friendship, UserSearchResult, UserSummary } from '../../types';

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
  const [filtro, setFiltro] = useState('');

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

  // Só a aba de amigos já feitos ganha filtro por nome (as outras são pedidos).
  const termo = filtro.trim().toLowerCase();
  const visiveis =
    estado === 'amigos' && termo
      ? rows.filter((f) => outro(f).nome.toLowerCase().includes(termo))
      : rows;

  function renderRow(f: Friendship) {
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
  }

  return (
    <Stack>
      {estado === 'amigos' && (
        <TextInput
          placeholder="Filtrar amigos por nome"
          leftSection={<IconSearch size={16} />}
          value={filtro}
          onChange={(e) => setFiltro(e.currentTarget.value)}
          maw={280}
        />
      )}
      {visiveis.length === 0 ? (
        <EmptyState title="Nenhum amigo encontrado com esse nome." />
      ) : (
        visiveis.map(renderRow)
      )}
    </Stack>
  );
}

// Botão/estado por resultado da busca: adiciona quem ainda não tem relação e
// mostra um selo para os demais estados (§3.1).
function FriendSearchAction({ u }: { u: UserSearchResult }) {
  const queryClient = useQueryClient();
  const send = useMutation({
    mutationFn: () => sendFriendRequest(u.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-search'] });
      queryClient.invalidateQueries({ queryKey: ['friendships'] });
      notifications.show({ color: 'green', message: 'Pedido de amizade enviado.' });
    },
    onError: (err) => notifications.show({ color: 'red', message: apiErrorMessage(err) }),
  });

  switch (u.amizade) {
    case 'amigos':
      return (
        <Badge variant="light" color="green" leftSection={<IconUserCheck size={12} />}>
          Amigos
        </Badge>
      );
    case 'pedido_enviado':
      return (
        <Badge variant="light" color="gray">
          Pedido enviado
        </Badge>
      );
    case 'pedido_recebido':
      return (
        <Badge variant="light" color="blue">
          Pedido recebido
        </Badge>
      );
    default:
      return (
        <Button
          size="xs"
          leftSection={<IconUserPlus size={14} />}
          onClick={() => send.mutate()}
          loading={send.isPending}
        >
          Adicionar
        </Button>
      );
  }
}

function SearchFriendsModal({ opened, onClose }: { opened: boolean; onClose: () => void }) {
  const [termo, setTermo] = useState('');
  const [debounced] = useDebouncedValue(termo, 300);
  const busca = debounced.trim();
  const habilitado = busca.length >= 2;

  const { data, isFetching } = useQuery({
    queryKey: ['user-search', busca],
    queryFn: () => searchUsers(busca),
    enabled: habilitado,
  });

  const rows = data?.results ?? [];

  function handleClose() {
    setTermo('');
    onClose();
  }

  return (
    <Modal opened={opened} onClose={handleClose} title="Adicionar amigo" size="md">
      <Stack>
        <TextInput
          placeholder="Nome do usuário"
          leftSection={<IconSearch size={16} />}
          value={termo}
          onChange={(e) => setTermo(e.currentTarget.value)}
          data-autofocus
        />
        {!habilitado ? (
          <Text c="dimmed" size="sm">
            Digite ao menos 2 caracteres para buscar.
          </Text>
        ) : isFetching ? (
          <Text c="dimmed" size="sm">
            Buscando…
          </Text>
        ) : rows.length === 0 ? (
          <Text c="dimmed" size="sm">
            Nenhum usuário encontrado.
          </Text>
        ) : (
          rows.map((u) => (
            <UserLine key={u.id} u={u}>
              <FriendSearchAction u={u} />
            </UserLine>
          ))
        )}
      </Stack>
    </Modal>
  );
}

export function FriendsPage() {
  const [searchOpened, { open, close }] = useDisclosure(false);
  return (
    <Stack gap="lg">
      <Group justify="space-between">
        <Title order={2}>Amigos</Title>
        <Button leftSection={<IconUserPlus size={16} />} onClick={open}>
          Adicionar amigo
        </Button>
      </Group>
      <SearchFriendsModal opened={searchOpened} onClose={close} />
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
