import { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Button,
  Card,
  Group,
  MultiSelect,
  NumberInput,
  Select,
  Stack,
  Textarea,
  TextInput,
  Title,
} from '@mantine/core';
import { DateInput } from '@mantine/dates';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { IconBrandSteam } from '@tabler/icons-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import dayjs from 'dayjs';
import {
  createGame,
  getGame,
  listTaxonomy,
  steamPreview,
  updateGame,
  type GameWritePayload,
} from '../../api/games';
import { apiErrorMessage } from '../../api/client';
import type { NamedRef } from '../../types';

function toOptions(items: NamedRef[] | undefined) {
  return (items ?? []).map((it) => ({ value: String(it.id), label: it.nome }));
}

function toDate(iso: string | null | undefined): Date | null {
  return iso ? new Date(`${iso}T00:00:00`) : null;
}

function toISO(date: Date | null): string | null {
  return date ? dayjs(date).format('YYYY-MM-DD') : null;
}

export function AdminGameFormPage() {
  const { id } = useParams();
  const isEdit = !!id;
  const gameId = Number(id);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const genres = useQuery({ queryKey: ['tax', 'genres'], queryFn: () => listTaxonomy('genres') });
  const platforms = useQuery({ queryKey: ['tax', 'platforms'], queryFn: () => listTaxonomy('platforms') });
  const developers = useQuery({ queryKey: ['tax', 'developers'], queryFn: () => listTaxonomy('developers') });
  const publishers = useQuery({ queryKey: ['tax', 'publishers'], queryFn: () => listTaxonomy('publishers') });

  const gameQuery = useQuery({
    queryKey: ['game', gameId],
    queryFn: () => getGame(gameId),
    enabled: isEdit && Number.isFinite(gameId),
  });

  const form = useForm({
    initialValues: {
      titulo: '',
      capa_url: '',
      banner_url: '',
      ano_lancamento: '' as number | string,
      data_lancamento: null as Date | null,
      sinopse: '',
      status_publicacao: 'rascunho' as 'rascunho' | 'publicado',
      steam_appid: '' as number | string,
      rawg_id: '' as number | string,
      genre_ids: [] as string[],
      platform_ids: [] as string[],
      developer_ids: [] as string[],
      publisher_ids: [] as string[],
    },
    validate: {
      titulo: (v) => (v.trim() ? null : 'Informe o título'),
    },
  });

  // Prefill ao carregar o jogo em modo edição.
  useEffect(() => {
    const g = gameQuery.data;
    if (!g) return;
    form.setValues({
      titulo: g.titulo,
      capa_url: g.capa_url ?? '',
      banner_url: g.banner_url ?? '',
      ano_lancamento: g.ano_lancamento ?? '',
      data_lancamento: toDate(g.data_lancamento),
      sinopse: g.sinopse ?? '',
      status_publicacao: g.status_publicacao,
      steam_appid: g.steam_appid ?? '',
      rawg_id: g.rawg_id ?? '',
      genre_ids: g.genres.map((x) => String(x.id)),
      platform_ids: g.platforms.map((x) => String(x.id)),
      developer_ids: g.developers.map((x) => String(x.id)),
      publisher_ids: g.publishers.map((x) => String(x.id)),
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [gameQuery.data]);

  // Autofill pela Storefront da Steam: preenche o form para revisão antes de salvar.
  const steamMutation = useMutation({
    mutationFn: (appid: number) => steamPreview(appid),
    onSuccess: async (data) => {
      if (data.existing_game_id && !isEdit) {
        notifications.show({
          color: 'yellow',
          message: 'Este jogo já está no catálogo. Abrindo para edição.',
        });
        navigate(`/admin/games/${data.existing_game_id}/edit`);
        return;
      }
      // Recarrega as taxonomias para incluir as recém-criadas (get_or_create no backend).
      await queryClient.invalidateQueries({ queryKey: ['tax'] });
      form.setValues({
        titulo: data.titulo || form.values.titulo,
        sinopse: data.sinopse ?? '',
        ano_lancamento: data.ano_lancamento ?? '',
        data_lancamento: toDate(data.data_lancamento),
        capa_url: data.capa_url ?? '',
        banner_url: data.banner_url ?? '',
        steam_appid: data.steam_appid,
        rawg_id: data.rawg_id ?? '',
        genre_ids: data.genres.map((g) => String(g.id)),
        platform_ids: data.platforms.map((g) => String(g.id)),
        developer_ids: data.developers.map((g) => String(g.id)),
        publisher_ids: data.publishers.map((g) => String(g.id)),
      });
      notifications.show({
        color: data.data_lancamento ? 'green' : 'yellow',
        message: data.data_lancamento
          ? 'Dados da Steam e data de lançamento (RAWG) carregados. Revise e salve.'
          : 'Dados da Steam carregados. Revise e salve (data de lançamento não encontrada na RAWG).',
      });
    },
    onError: (err) => notifications.show({ color: 'red', message: apiErrorMessage(err) }),
  });

  function handleSteamFetch() {
    const appid = Number(form.values.steam_appid);
    if (!appid) {
      notifications.show({ color: 'yellow', message: 'Informe o Steam AppID antes de buscar.' });
      return;
    }
    steamMutation.mutate(appid);
  }

  const mutation = useMutation({
    mutationFn: (values: typeof form.values) => {
      const payload: GameWritePayload = {
        titulo: values.titulo,
        capa_url: values.capa_url.trim() || null,
        banner_url: values.banner_url.trim() || null,
        ano_lancamento: values.ano_lancamento === '' ? null : Number(values.ano_lancamento),
        data_lancamento: toISO(values.data_lancamento),
        sinopse: values.sinopse.trim() || null,
        status_publicacao: values.status_publicacao,
        steam_appid: values.steam_appid === '' ? null : Number(values.steam_appid),
        rawg_id: values.rawg_id === '' ? null : Number(values.rawg_id),
        genre_ids: values.genre_ids.map(Number),
        platform_ids: values.platform_ids.map(Number),
        developer_ids: values.developer_ids.map(Number),
        publisher_ids: values.publisher_ids.map(Number),
      };
      return isEdit ? updateGame(gameId, payload) : createGame(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'games'] });
      queryClient.invalidateQueries({ queryKey: ['games'] });
      if (isEdit) queryClient.invalidateQueries({ queryKey: ['game', gameId] });
      notifications.show({ color: 'green', message: isEdit ? 'Jogo atualizado.' : 'Jogo criado.' });
      navigate('/admin/games');
    },
    onError: (err) => notifications.show({ color: 'red', message: apiErrorMessage(err) }),
  });

  return (
    <Stack gap="lg" maw={720}>
      <Title order={2}>{isEdit ? 'Editar jogo' : 'Novo jogo'}</Title>
      <Card withBorder radius="md" p="lg">
        <form onSubmit={form.onSubmit((v) => mutation.mutate(v))}>
          <Stack>
            <TextInput label="Título" withAsterisk {...form.getInputProps('titulo')} />
            <Group grow align="flex-end">
              <NumberInput
                label="Ano de lançamento"
                min={1950}
                max={2100}
                {...form.getInputProps('ano_lancamento')}
              />
              <div>
                <DateInput
                  label="Data de lançamento"
                  description={form.values.rawg_id ? `RAWG #${form.values.rawg_id}` : undefined}
                  placeholder="Vem da RAWG ao buscar da Steam"
                  valueFormat="DD/MM/YYYY"
                  clearable
                  {...form.getInputProps('data_lancamento')}
                />
              </div>
              <Select
                label="Status de publicação"
                data={[
                  { value: 'rascunho', label: 'Rascunho' },
                  { value: 'publicado', label: 'Publicado' },
                ]}
                allowDeselect={false}
                {...form.getInputProps('status_publicacao')}
              />
            </Group>
            <TextInput label="URL da capa" placeholder="https://..." {...form.getInputProps('capa_url')} />
            <TextInput label="URL do banner" placeholder="https://..." {...form.getInputProps('banner_url')} />
            <Group align="flex-end" gap="sm">
              <NumberInput
                label="Steam AppID"
                min={0}
                style={{ flex: 1 }}
                {...form.getInputProps('steam_appid')}
              />
              <Button
                variant="light"
                color="indigo"
                leftSection={<IconBrandSteam size={16} />}
                onClick={handleSteamFetch}
                loading={steamMutation.isPending}
              >
                Buscar da Steam
              </Button>
            </Group>
            <Textarea label="Sinopse" autosize minRows={4} {...form.getInputProps('sinopse')} />

            <MultiSelect
              label="Gêneros"
              searchable
              data={toOptions(genres.data)}
              {...form.getInputProps('genre_ids')}
            />
            <MultiSelect
              label="Plataformas"
              searchable
              data={toOptions(platforms.data)}
              {...form.getInputProps('platform_ids')}
            />
            <MultiSelect
              label="Desenvolvedoras"
              searchable
              data={toOptions(developers.data)}
              {...form.getInputProps('developer_ids')}
            />
            <MultiSelect
              label="Publicadoras"
              searchable
              data={toOptions(publishers.data)}
              {...form.getInputProps('publisher_ids')}
            />

            <Group justify="flex-end" mt="sm">
              <Button variant="default" onClick={() => navigate('/admin/games')}>
                Cancelar
              </Button>
              <Button type="submit" loading={mutation.isPending}>
                {isEdit ? 'Salvar' : 'Criar'}
              </Button>
            </Group>
          </Stack>
        </form>
      </Card>
    </Stack>
  );
}
