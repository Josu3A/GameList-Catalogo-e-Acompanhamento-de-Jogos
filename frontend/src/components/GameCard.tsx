import { Link } from 'react-router-dom';
import { AspectRatio, Card, Group, Image, Stack, Text } from '@mantine/core';
import { IconDeviceGamepad2 } from '@tabler/icons-react';
import type { GameSummary } from '../types';

interface GameCardProps {
  game: GameSummary;
  /** Badge opcional no canto (ex.: status na lista). */
  badge?: React.ReactNode;
}

export function GameCard({ game, badge }: GameCardProps) {
  // Capa vertical (biblioteca Steam) por padrão; se faltar/404 cai no capsule.
  const cover = game.capa_vertical_url ?? game.capa_url;
  return (
    <Card
      component={Link}
      to={`/games/${game.id}`}
      padding="sm"
      radius="md"
      withBorder
      style={{ textDecoration: 'none', color: 'inherit', height: '100%' }}
    >
      <Card.Section>
        <AspectRatio ratio={3 / 4}>
          {cover ? (
            <Image
              src={cover}
              fallbackSrc={game.capa_url ?? undefined}
              alt={game.titulo}
              fit="cover"
            />
          ) : (
            <Stack align="center" justify="center" bg="dark.5" gap={4}>
              <IconDeviceGamepad2 size={36} opacity={0.5} />
              <Text size="xs" c="dimmed" ta="center" px="xs" lineClamp={2}>
                {game.titulo}
              </Text>
            </Stack>
          )}
        </AspectRatio>
      </Card.Section>

      <Stack gap={4} mt="sm">
        <Text fw={600} size="sm" lineClamp={2}>
          {game.titulo}
        </Text>
        {game.ano_lancamento && (
          <Text size="xs" c="dimmed">
            {game.ano_lancamento}
          </Text>
        )}
        {badge && <div>{badge}</div>}
      </Stack>
    </Card>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  /** Botão(ões) de ação, ex.: "Adicionar jogo" — para a tela não ficar num beco sem saída. */
  action?: React.ReactNode;
}) {
  return (
    <Stack align="center" py="xl" gap="xs">
      <IconDeviceGamepad2 size={48} opacity={0.4} />
      <Text fw={600}>{title}</Text>
      {description && (
        <Text size="sm" c="dimmed" ta="center" maw={420}>
          {description}
        </Text>
      )}
      {action && (
        <Group justify="center" mt="xs">
          {action}
        </Group>
      )}
    </Stack>
  );
}
