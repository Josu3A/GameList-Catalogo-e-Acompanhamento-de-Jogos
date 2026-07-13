import { Link } from 'react-router-dom';
import {
  Avatar,
  Button,
  Card,
  Group,
  Indicator,
  Stack,
  Text,
  Title,
} from '@mantine/core';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { notifications } from '@mantine/notifications';
import {
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from '../../api/social';
import { apiErrorMessage } from '../../api/client';
import { EmptyState } from '../../components/GameCard';
import { notificationText, formatDate } from '../../lib/labels';
import { profileLink } from '../../lib/profileUrl';

export function NotificationsPage() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['notifications', 'list'],
    queryFn: listNotifications,
  });

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ['notifications'] });
  }

  const markRead = useMutation({
    mutationFn: (id: number) => markNotificationRead(id),
    onSuccess: invalidate,
    onError: (err) => notifications.show({ color: 'red', message: apiErrorMessage(err) }),
  });

  const markAll = useMutation({
    mutationFn: markAllNotificationsRead,
    onSuccess: invalidate,
    onError: (err) => notifications.show({ color: 'red', message: apiErrorMessage(err) }),
  });

  const rows = data?.results ?? [];
  const hasUnread = rows.some((n) => !n.lida);

  return (
    <Stack gap="lg">
      <Group justify="space-between">
        <Title order={2}>Notificações</Title>
        <Button
          variant="default"
          size="sm"
          disabled={!hasUnread}
          loading={markAll.isPending}
          onClick={() => markAll.mutate()}
        >
          Marcar todas como lidas
        </Button>
      </Group>

      {isLoading ? (
        <Text c="dimmed">Carregando…</Text>
      ) : rows.length === 0 ? (
        <EmptyState title="Nenhuma notificação." />
      ) : (
        <Stack gap="xs">
          {rows.map((n) => {
            const actorLink = n.actor ? profileLink(n.actor) : undefined;
            return (
              <Card
                key={n.id}
                withBorder
                radius="md"
                p="sm"
                bg={n.lida ? undefined : 'var(--mantine-color-dark-6)'}
              >
                <Group justify="space-between" wrap="nowrap">
                  <Group gap="sm" wrap="nowrap">
                    <Indicator disabled={n.lida} size={8} color="violet">
                      <Avatar
                        src={n.actor?.avatar_url ?? undefined}
                        radius="xl"
                        {...(actorLink
                          ? { renderRoot: (props: Record<string, unknown>) => <Link {...actorLink} {...props} /> }
                          : {})}
                      >
                        {n.actor?.nome.slice(0, 1).toUpperCase() ?? '?'}
                      </Avatar>
                    </Indicator>
                    <div>
                      <Text size="sm">{notificationText(n.tipo, n.actor?.nome)}</Text>
                      <Text size="xs" c="dimmed">
                        {formatDate(n.created_at)}
                      </Text>
                    </div>
                  </Group>
                  {!n.lida && (
                    <Button
                      size="xs"
                      variant="subtle"
                      onClick={() => markRead.mutate(n.id)}
                    >
                      Marcar lida
                    </Button>
                  )}
                </Group>
              </Card>
            );
          })}
        </Stack>
      )}
    </Stack>
  );
}
