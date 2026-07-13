import { Link } from 'react-router-dom';
import {
  Button,
  Group,
  Paper,
  SimpleGrid,
  Skeleton,
  Stack,
  Text,
  Title,
} from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { listGames } from '../../api/games';
import { GameCard, EmptyState } from '../../components/GameCard';
import { useAuth } from '../../auth/AuthContext';

export function HomePage() {
  const { user } = useAuth();
  const { data, isLoading } = useQuery({
    queryKey: ['games', 'home'],
    queryFn: () => listGames({ ordering: '-created_at' }),
  });

  const games = data?.results ?? [];

  return (
    <Stack gap="xl">
      <Paper p="xl" radius="md" withBorder>
        <Stack gap="sm" align="flex-start">
          <Title order={1}>Sua coleção de jogos, organizada.</Title>
          <Text c="dimmed" maw={620}>
            Navegue pelo catálogo, monte sua lista pessoal com status, notas e horas
            jogadas, destaque suas platinas e acompanhe amigos.
          </Text>
          <Group mt="sm">
            <Button component={Link} to="/games" size="md">
              Explorar catálogo
            </Button>
            {!user && (
              <Button component={Link} to="/register" variant="default" size="md">
                Criar conta
              </Button>
            )}
          </Group>
        </Stack>
      </Paper>

      <Stack gap="sm">
        <Title order={3}>Adicionados recentemente</Title>
        {isLoading ? (
          <SimpleGrid cols={{ base: 2, sm: 3, md: 5 }}>
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} height={260} radius="md" />
            ))}
          </SimpleGrid>
        ) : games.length === 0 ? (
          <EmptyState title="Nenhum jogo no catálogo ainda." />
        ) : (
          <SimpleGrid cols={{ base: 2, sm: 3, md: 5 }}>
            {games.slice(0, 10).map((game) => (
              <GameCard key={game.id} game={game} />
            ))}
          </SimpleGrid>
        )}
      </Stack>
    </Stack>
  );
}
