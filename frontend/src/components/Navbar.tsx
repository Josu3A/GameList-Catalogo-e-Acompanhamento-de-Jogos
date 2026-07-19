import { Link, useNavigate } from 'react-router-dom';
import {
  ActionIcon,
  Avatar,
  Button,
  Group,
  Indicator,
  Menu,
  Text,
} from '@mantine/core';
import {
  IconBell,
  IconList,
  IconLogout,
  IconSettings,
  IconShield,
  IconUser,
  IconUsers,
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../auth/AuthContext';
import { unreadCount } from '../api/social';
import { profileLink } from '../lib/profileUrl';

export function Navbar() {
  const { user, isAdmin, logout } = useAuth();
  const navigate = useNavigate();

  const { data: unread = 0 } = useQuery({
    queryKey: ['notifications', 'unread'],
    queryFn: unreadCount,
    enabled: !!user,
    refetchInterval: 60_000,
  });

  async function handleLogout() {
    await logout();
    navigate('/');
  }

  return (
    <Group h="100%" px="md" justify="space-between" wrap="nowrap">
      <Group gap="lg" wrap="nowrap">
        <Group
          gap={6}
          style={{ textDecoration: 'none', color: 'inherit' }}
          renderRoot={(props) => <Link to="/" {...props} />}
        >
          <img
            src="/logo.png"
            alt="GameCheck"
            width={30}
            height={30}
            style={{ display: 'block' }}
          />
          <Text fw={700} size="lg">
            GameCheck
          </Text>
        </Group>
        <Button component={Link} to="/games" variant="subtle" size="sm">
          Catálogo
        </Button>
        {user && (
          <>
            <Button component={Link} to="/my-list" variant="subtle" size="sm">
              Minha lista
            </Button>
            <Button component={Link} to="/lists" variant="subtle" size="sm">
              Listas
            </Button>
            <Button component={Link} to="/friends" variant="subtle" size="sm">
              Amigos
            </Button>
          </>
        )}
      </Group>

      <Group gap="sm" wrap="nowrap">
        {user ? (
          <>
            <Indicator
              disabled={unread === 0}
              label={unread > 9 ? '9+' : unread}
              size={16}
              offset={4}
            >
              <ActionIcon
                component={Link}
                to="/notifications"
                variant="subtle"
                size="lg"
                aria-label="Notificações"
              >
                <IconBell size={20} />
              </ActionIcon>
            </Indicator>

            <Menu shadow="md" width={220} position="bottom-end">
              <Menu.Target>
                <Group gap={8} style={{ cursor: 'pointer' }} wrap="nowrap">
                  <Avatar src={user.avatar_url ?? undefined} radius="xl" size={32}>
                    {user.nome.slice(0, 1).toUpperCase()}
                  </Avatar>
                  <Text size="sm" visibleFrom="sm">
                    {user.nome}
                  </Text>
                </Group>
              </Menu.Target>
              <Menu.Dropdown>
                <Menu.Item
                  leftSection={<IconUser size={16} />}
                  component={Link}
                  {...profileLink(user)}
                >
                  Meu perfil
                </Menu.Item>
                <Menu.Item
                  leftSection={<IconSettings size={16} />}
                  component={Link}
                  to="/settings/profile"
                >
                  Editar perfil
                </Menu.Item>
                <Menu.Item
                  leftSection={<IconList size={16} />}
                  component={Link}
                  to="/lists"
                >
                  Minhas listas
                </Menu.Item>
                {isAdmin && (
                  <>
                    <Menu.Divider />
                    <Menu.Label>Administração</Menu.Label>
                    <Menu.Item
                      leftSection={<IconShield size={16} />}
                      component={Link}
                      to="/admin/games"
                    >
                      Catálogo (admin)
                    </Menu.Item>
                    <Menu.Item
                      leftSection={<IconUsers size={16} />}
                      component={Link}
                      to="/admin/taxonomies"
                    >
                      Gêneros / plataformas
                    </Menu.Item>
                  </>
                )}
                <Menu.Divider />
                <Menu.Item
                  color="red"
                  leftSection={<IconLogout size={16} />}
                  onClick={handleLogout}
                >
                  Sair
                </Menu.Item>
              </Menu.Dropdown>
            </Menu>
          </>
        ) : (
          <>
            <Button component={Link} to="/login" variant="default" size="sm">
              Entrar
            </Button>
            <Button component={Link} to="/register" size="sm">
              Criar conta
            </Button>
          </>
        )}
      </Group>
    </Group>
  );
}
