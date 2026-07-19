import { Link } from 'react-router-dom';
import { AspectRatio, Card, Image, Stack, Text } from '@mantine/core';
import { IconCalendarEvent } from '@tabler/icons-react';
import dayjs from 'dayjs';
import 'dayjs/locale/pt-br';
import type { ProximoLancamento } from '../types';

dayjs.locale('pt-br');

interface UpcomingGameCardProps {
  item: ProximoLancamento;
}

/** Card do carrossel de próximos lançamentos (Home).
 *
 * Com `game_id` (casou com o catálogo local): card clicável, linka pra
 * /games/:id. Sem `game_id`: card só informativo — a RAWG não tem uma rota
 * interna própria, então não deve linkar pra lugar nenhum.
 */
export function UpcomingGameCard({ item }: UpcomingGameCardProps) {
  const conteudo = (
    <>
      <Card.Section>
        {/* RAWG só tem background_image (paisagem) — sem capa vertical como a
            Steam. Usar 3/4 aqui cortava a imagem de forma estranha. */}
        <AspectRatio ratio={16 / 9}>
          {item.capa_url ? (
            <Image src={item.capa_url} alt={item.nome} fit="cover" />
          ) : (
            <Stack align="center" justify="center" bg="dark.5" gap={4}>
              <IconCalendarEvent size={36} opacity={0.5} />
              <Text size="xs" c="dimmed" ta="center" px="xs" lineClamp={2}>
                {item.nome}
              </Text>
            </Stack>
          )}
        </AspectRatio>
      </Card.Section>

      <Stack gap={4} mt="sm">
        <Text fw={600} size="sm" lineClamp={2} lh="1.4em" mih="2.8em">
          {item.nome}
        </Text>
        <Text size="xs" c="dimmed">
          Lança em {dayjs(item.data_lancamento).format('D MMM YYYY')}
        </Text>
      </Stack>
    </>
  );

  if (item.game_id) {
    return (
      <Card
        component={Link}
        to={`/games/${item.game_id}`}
        padding="sm"
        radius="md"
        withBorder
        style={{ textDecoration: 'none', color: 'inherit', height: '100%' }}
      >
        {conteudo}
      </Card>
    );
  }

  return (
    <Card padding="sm" radius="md" withBorder style={{ height: '100%' }}>
      {conteudo}
    </Card>
  );
}
