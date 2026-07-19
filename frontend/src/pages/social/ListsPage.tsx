import { Link } from 'react-router-dom';
import {
  ActionIcon,
  Badge,
  Button,
  Card,
  Group,
  Modal,
  SimpleGrid,
  Stack,
  Switch,
  Text,
  Textarea,
  TextInput,
  Title,
} from '@mantine/core';
import { IconPlus, IconTrash } from '@tabler/icons-react';
import { useDisclosure } from '@mantine/hooks';
import { useForm } from '@mantine/form';
import { modals } from '@mantine/modals';
import { notifications } from '@mantine/notifications';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createList, deleteList, listMyLists } from '../../api/social';
import { apiErrorMessage } from '../../api/client';
import { EmptyState } from '../../components/GameCard';
import type { ListSummary } from '../../types';

export function ListsPage() {
  const queryClient = useQueryClient();
  const [opened, modal] = useDisclosure(false);

  const { data, isLoading } = useQuery({
    queryKey: ['lists', 'mine'],
    queryFn: listMyLists,
  });

  const form = useForm({
    initialValues: { nome: '', descricao: '', publica: true },
    validate: { nome: (v) => (v.trim() ? null : 'Informe um nome') },
  });

  const create = useMutation({
    mutationFn: (values: typeof form.values) =>
      createList({
        nome: values.nome,
        descricao: values.descricao.trim() || null,
        publica: values.publica,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lists'] });
      notifications.show({ color: 'green', message: 'Lista criada.' });
      form.reset();
      modal.close();
    },
    onError: (err) => notifications.show({ color: 'red', message: apiErrorMessage(err) }),
  });

  const remove = useMutation({
    mutationFn: (id: number) => deleteList(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lists'] });
      notifications.show({ color: 'green', message: 'Lista excluída.' });
    },
    onError: (err) => notifications.show({ color: 'red', message: apiErrorMessage(err) }),
  });

  function confirmRemove(l: ListSummary) {
    modals.openConfirmModal({
      title: 'Excluir lista',
      children: <Text size="sm">Excluir a lista “{l.nome}”?</Text>,
      labels: { confirm: 'Excluir', cancel: 'Cancelar' },
      confirmProps: { color: 'red' },
      onConfirm: () => remove.mutate(l.id),
    });
  }

  const lists = data?.results ?? [];

  return (
    <Stack gap="lg">
      <Group justify="space-between">
        <Title order={2}>Minhas listas</Title>
        {/* Com a lista vazia, o CTA fica no próprio estado vazio (abaixo) para não
            duplicar o botão; o do topo só aparece quando já há listas para somar. */}
        {lists.length > 0 && (
          <Button leftSection={<IconPlus size={16} />} onClick={modal.open}>
            Nova lista
          </Button>
        )}
      </Group>

      {isLoading ? (
        <Text c="dimmed">Carregando…</Text>
      ) : lists.length === 0 ? (
        <EmptyState
          title="Você ainda não criou listas"
          description="Crie coleções como “Top 10 RPGs” e adicione jogos do catálogo."
          action={
            <Button leftSection={<IconPlus size={16} />} onClick={modal.open}>
              Criar lista
            </Button>
          }
        />
      ) : (
        <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }}>
          {lists.map((l) => (
            <Card key={l.id} withBorder radius="md" p="md">
              <Group justify="space-between" align="flex-start" wrap="nowrap">
                <Stack
                  gap={4}
                  style={{ textDecoration: 'none', color: 'inherit', flex: 1, minWidth: 0 }}
                  renderRoot={(props) => <Link to={`/lists/${l.id}`} {...props} />}
                >
                  <Group gap={6}>
                    <Text fw={600}>{l.nome}</Text>
                    {!l.publica && (
                      <Badge size="xs" variant="light" color="gray">
                        privada
                      </Badge>
                    )}
                  </Group>
                  {l.descricao && (
                    <Text size="sm" c="dimmed" lineClamp={2}>
                      {l.descricao}
                    </Text>
                  )}
                  <Text size="xs" c="dimmed">
                    {l.total_itens} {l.total_itens === 1 ? 'jogo' : 'jogos'}
                  </Text>
                </Stack>
                <ActionIcon
                  variant="subtle"
                  color="red"
                  aria-label="Excluir lista"
                  onClick={() => confirmRemove(l)}
                >
                  <IconTrash size={16} />
                </ActionIcon>
              </Group>
            </Card>
          ))}
        </SimpleGrid>
      )}

      <Modal opened={opened} onClose={modal.close} title="Nova lista" centered>
        <form onSubmit={form.onSubmit((v) => create.mutate(v))}>
          <Stack>
            <TextInput label="Nome" withAsterisk {...form.getInputProps('nome')} />
            <Textarea label="Descrição" autosize minRows={2} {...form.getInputProps('descricao')} />
            <Switch
              label="Lista pública"
              checked={form.values.publica}
              {...form.getInputProps('publica', { type: 'checkbox' })}
            />
            <Group justify="flex-end" mt="sm">
              <Button variant="default" onClick={modal.close}>
                Cancelar
              </Button>
              <Button type="submit" loading={create.isPending}>
                Criar
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>
    </Stack>
  );
}
