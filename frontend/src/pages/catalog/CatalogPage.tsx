import { useState } from 'react';
import {
  Center,
  Group,
  Pagination,
  Select,
  SimpleGrid,
  Skeleton,
  Stack,
  TextInput,
  Title,
} from '@mantine/core';
import { IconSearch } from '@tabler/icons-react';
import { useDebouncedValue } from '@mantine/hooks';
import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { listGames, listTaxonomy } from '../../api/games';
import { GameCard, EmptyState } from '../../components/GameCard';

const PAGE_SIZE = 20;

const ORDERING = [
  { value: 'titulo', label: 'Título (A→Z)' },
  { value: '-titulo', label: 'Título (Z→A)' },
  { value: '-ano_lancamento', label: 'Mais recentes' },
  { value: 'ano_lancamento', label: 'Mais antigos' },
];

export function CatalogPage() {
  const [search, setSearch] = useState('');
  const [debounced] = useDebouncedValue(search, 300);
  const [genero, setGenero] = useState<string | null>(null);
  const [plataforma, setPlataforma] = useState<string | null>(null);
  const [ordering, setOrdering] = useState<string>('titulo');
  const [page, setPage] = useState(1);

  const genres = useQuery({ queryKey: ['tax', 'genres'], queryFn: () => listTaxonomy('genres') });
  const platforms = useQuery({ queryKey: ['tax', 'platforms'], queryFn: () => listTaxonomy('platforms') });

  const { data, isLoading, isPlaceholderData } = useQuery({
    queryKey: ['games', 'catalog', { debounced, genero, plataforma, ordering, page }],
    queryFn: () =>
      listGames({
        search: debounced || undefined,
        genero: genero ? Number(genero) : undefined,
        plataforma: plataforma ? Number(plataforma) : undefined,
        ordering,
        page,
      }),
    placeholderData: keepPreviousData,
  });

  // Qualquer mudança de filtro volta para a página 1.
  function resetTo(setter: (v: string | null) => void) {
    return (value: string | null) => {
      setter(value);
      setPage(1);
    };
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.count / PAGE_SIZE)) : 1;
  const games = data?.results ?? [];

  return (
    <Stack gap="lg">
      <Title order={2}>Catálogo</Title>

      <Group align="flex-end" wrap="wrap">
        <TextInput
          label="Buscar"
          placeholder="Título do jogo"
          leftSection={<IconSearch size={16} />}
          value={search}
          onChange={(e) => {
            setSearch(e.currentTarget.value);
            setPage(1);
          }}
          w={240}
        />
        <Select
          label="Gênero"
          placeholder="Todos"
          clearable
          data={(genres.data ?? []).map((g) => ({ value: String(g.id), label: g.nome }))}
          value={genero}
          onChange={resetTo(setGenero)}
          w={180}
        />
        <Select
          label="Plataforma"
          placeholder="Todas"
          clearable
          data={(platforms.data ?? []).map((p) => ({ value: String(p.id), label: p.nome }))}
          value={plataforma}
          onChange={resetTo(setPlataforma)}
          w={180}
        />
        <Select
          label="Ordenar"
          data={ORDERING}
          value={ordering}
          onChange={(v) => {
            setOrdering(v ?? 'titulo');
            setPage(1);
          }}
          w={180}
          allowDeselect={false}
        />
      </Group>

      {isLoading ? (
        <SimpleGrid cols={{ base: 2, sm: 3, md: 5 }}>
          {Array.from({ length: 10 }).map((_, i) => (
            <Skeleton key={i} height={260} radius="md" />
          ))}
        </SimpleGrid>
      ) : games.length === 0 ? (
        <EmptyState
          title="Nenhum jogo encontrado"
          description="Tente ajustar a busca ou os filtros."
        />
      ) : (
        <SimpleGrid
          cols={{ base: 2, sm: 3, md: 5 }}
          style={{ opacity: isPlaceholderData ? 0.6 : 1 }}
        >
          {games.map((game) => (
            <GameCard key={game.id} game={game} />
          ))}
        </SimpleGrid>
      )}

      {totalPages > 1 && (
        <Center>
          <Pagination total={totalPages} value={page} onChange={setPage} />
        </Center>
      )}
    </Stack>
  );
}
