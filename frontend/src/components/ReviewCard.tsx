import { Link } from 'react-router-dom';
import { ActionIcon, Avatar, Badge, Group, Paper, Stack, Text } from '@mantine/core';
import { IconHeart, IconHeartFilled, IconStarFilled } from '@tabler/icons-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { notifications } from '@mantine/notifications';
import { likeReview, unlikeReview } from '../api/social';
import { apiErrorMessage } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import { formatDate } from '../lib/labels';
import { profileLink } from '../lib/profileUrl';
import type { Review } from '../types';

interface Props {
  review: Review;
  /** chave de query a invalidar após curtir/descurtir. */
  invalidateKey: unknown[];
  /** mostra o título do jogo (para feeds fora da página do jogo). */
  showGame?: boolean;
}

export function ReviewCard({ review, invalidateKey, showGame }: Props) {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const toggle = useMutation({
    mutationFn: () =>
      review.liked_by_me ? unlikeReview(review.id) : likeReview(review.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: invalidateKey }),
    onError: (err) => notifications.show({ color: 'red', message: apiErrorMessage(err) }),
  });

  return (
    <Paper withBorder radius="md" p="md">
      <Stack gap="xs">
        <Group justify="space-between" wrap="nowrap">
          <Group gap="sm" wrap="nowrap">
            <Avatar src={review.user.avatar_url ?? undefined} radius="xl" size={36}>
              {review.user.nome.slice(0, 1).toUpperCase()}
            </Avatar>
            <div>
              <Text
                fw={600}
                size="sm"
                component={Link}
                {...profileLink(review.user)}
                style={{ textDecoration: 'none', color: 'inherit' }}
              >
                {review.user.nome}
              </Text>
              <Text size="xs" c="dimmed">
                {showGame ? `${review.game.titulo} · ` : ''}
                {formatDate(review.created_at)}
              </Text>
            </div>
          </Group>
          {review.nota !== null && (
            <Badge
              variant="light"
              color="yellow"
              leftSection={<IconStarFilled size={12} />}
            >
              {review.nota}
            </Badge>
          )}
        </Group>

        {review.review && <Text size="sm">{review.review}</Text>}

        <Group gap={6}>
          <ActionIcon
            variant="subtle"
            color={review.liked_by_me ? 'red' : 'gray'}
            disabled={!user}
            loading={toggle.isPending}
            onClick={() => toggle.mutate()}
            aria-label="Curtir review"
          >
            {review.liked_by_me ? <IconHeartFilled size={18} /> : <IconHeart size={18} />}
          </ActionIcon>
          <Text size="sm" c="dimmed">
            {review.likes_count}
          </Text>
        </Group>
      </Stack>
    </Paper>
  );
}
