import { useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  Alert,
  Badge,
  BackgroundImage,
  Box,
  Button,
  Divider,
  Grid,
  Group,
  Image,
  Skeleton,
  Stack,
  Text,
  Title,
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { notifications } from '@mantine/notifications';
import { IconBrandSteam, IconPlus, IconTrophy } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { getGame } from '../../api/games';
import { steamAchievements } from '../../api/library';
import { listReviews } from '../../api/social';
import { apiErrorMessage } from '../../api/client';
import { useAuth } from '../../auth/AuthContext';
import { UserGameFormModal } from '../../components/UserGameFormModal';
import { ReviewCard } from '../../components/ReviewCard';
import { EmptyState } from '../../components/GameCard';
import type { SteamAchievementsResult } from '../../types';

function TagList({ label, items }: { label: string; items: { id: number; nome: string }[] }) {
  if (items.length === 0) return null;
  return (
    <Group gap="xs">
      <Text size="sm" c="dimmed" w={110}>
        {label}
      </Text>
      <Group gap={6}>
        {items.map((it) => (
          <Badge key={it.id} variant="light">
            {it.nome}
          </Badge>
        ))}
      </Group>
    </Group>
  );
}

export function GameDetailPage() {
  const { id } = useParams();
  const gameId = Number(id);
  const { user } = useAuth();
  const [modalOpen, modal] = useDisclosure(false);
  const [achLoading, setAchLoading] = useState(false);
  const [achResult, setAchResult] = useState<SteamAchievementsResult | null>(null);

  async function handleAchievements() {
    setAchLoading(true);
    try {
      const r = await steamAchievements(gameId);
      setAchResult(r);
      notifications.show({
        color: r.platinado ? 'yellow' : 'green',
        message: r.platinado
          ? 'Todas as conquistas! Jogo marcado como platinado.'
          : `Conquistas sincronizadas: ${r.desbloqueadas}/${r.total} (${r.percent}%).`,
      });
    } catch (err) {
      notifications.show({ color: 'red', message: apiErrorMessage(err) });
    } finally {
      setAchLoading(false);
    }
  }

  const { data: game, isLoading, isError } = useQuery({
    queryKey: ['game', gameId],
    queryFn: () => getGame(gameId),
    enabled: Number.isFinite(gameId),
  });

  const reviews = useQuery({
    queryKey: ['reviews', gameId],
    queryFn: () => listReviews(gameId),
    enabled: Number.isFinite(gameId),
  });

  if (isLoading) return <Skeleton height={400} radius="md" />;
  if (isError || !game) return <EmptyState title="Jogo não encontrado." />;

  // Artes da biblioteca Steam (verticais/largas) por padrão; caem no bruto.
  const cover = game.capa_vertical_url ?? game.capa_url;
  const banner = game.banner_hero_url ?? game.banner_url;

  return (
    <Stack gap="lg">
      {banner && (
        <BackgroundImage src={banner} radius="md" h={260}>
          <Box h={260} style={{ borderRadius: 8, background: 'rgba(0,0,0,0.35)' }} />
        </BackgroundImage>
      )}

      <Grid>
        <Grid.Col span={{ base: 12, sm: 4, md: 3 }}>
          {cover ? (
            <Image
              src={cover}
              fallbackSrc={game.capa_url ?? undefined}
              radius="md"
              alt={game.titulo}
            />
          ) : (
            <Skeleton height={320} radius="md" animate={false} />
          )}
        </Grid.Col>

        <Grid.Col span={{ base: 12, sm: 8, md: 9 }}>
          <Stack gap="sm">
            <Group justify="space-between" align="flex-start">
              <div>
                <Title order={2}>{game.titulo}</Title>
                {game.ano_lancamento && (
                  <Text c="dimmed">{game.ano_lancamento}</Text>
                )}
              </div>
              {game.status_publicacao === 'rascunho' && (
                <Badge color="orange" variant="light">
                  Rascunho
                </Badge>
              )}
            </Group>

            {(user || game.steam_appid) && (
              <Group>
                {user && (
                  <Button leftSection={<IconPlus size={16} />} onClick={modal.open}>
                    Adicionar à minha lista
                  </Button>
                )}
                {game.steam_appid && (
                  <Button
                    component="a"
                    href={`https://store.steampowered.com/app/${game.steam_appid}`}
                    target="_blank"
                    rel="noreferrer"
                    variant="light"
                    color="indigo"
                    leftSection={<IconBrandSteam size={16} />}
                  >
                    Ver na Steam
                  </Button>
                )}
                {user?.steam_id && game.steam_appid && (
                  <Button
                    variant="default"
                    leftSection={<IconTrophy size={16} />}
                    onClick={handleAchievements}
                    loading={achLoading}
                  >
                    Sincronizar conquistas
                  </Button>
                )}
              </Group>
            )}
            {achResult && (
              <Text size="sm" c="dimmed">
                Conquistas: {achResult.desbloqueadas}/{achResult.total} • {achResult.percent}%
                {achResult.platinado ? ' • platinado!' : ''}
              </Text>
            )}

            <Stack gap={6} mt="xs">
              <TagList label="Gêneros" items={game.genres} />
              <TagList label="Plataformas" items={game.platforms} />
              <TagList label="Desenvolvedoras" items={game.developers} />
              <TagList label="Publicadoras" items={game.publishers} />
            </Stack>

            {game.sinopse && (
              <>
                <Divider my="sm" />
                <Text style={{ whiteSpace: 'pre-line' }}>{game.sinopse}</Text>
              </>
            )}
          </Stack>
        </Grid.Col>
      </Grid>

      <Divider label="Reviews" labelPosition="center" />

      {reviews.isLoading ? (
        <Skeleton height={120} radius="md" />
      ) : reviews.data && reviews.data.results.length > 0 ? (
        <Stack>
          {reviews.data.results.map((r) => (
            <ReviewCard key={r.id} review={r} invalidateKey={['reviews', gameId]} />
          ))}
        </Stack>
      ) : (
        <Alert variant="light" color="gray">
          Ainda não há reviews para este jogo. Adicione-o à sua lista e escreva a primeira!
        </Alert>
      )}

      <UserGameFormModal
        opened={modalOpen}
        onClose={modal.close}
        gameId={game.id}
        gameTitulo={game.titulo}
      />
    </Stack>
  );
}
