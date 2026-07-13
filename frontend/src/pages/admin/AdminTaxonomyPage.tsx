import { useState } from 'react';
import {
  ActionIcon,
  Button,
  Card,
  Group,
  Stack,
  Table,
  Tabs,
  Text,
  TextInput,
  Title,
} from '@mantine/core';
import { IconCheck, IconEdit, IconPlus, IconTrash, IconX } from '@tabler/icons-react';
import { modals } from '@mantine/modals';
import { notifications } from '@mantine/notifications';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  createTaxonomy,
  deleteTaxonomy,
  listTaxonomy,
  updateTaxonomy,
  type Taxonomy,
} from '../../api/games';
import { apiErrorMessage } from '../../api/client';
import type { NamedRef } from '../../types';

const KINDS: { value: Taxonomy; label: string }[] = [
  { value: 'genres', label: 'Gêneros' },
  { value: 'platforms', label: 'Plataformas' },
  { value: 'developers', label: 'Desenvolvedoras' },
  { value: 'publishers', label: 'Publicadoras' },
];

function TaxonomyManager({ kind }: { kind: Taxonomy }) {
  const queryClient = useQueryClient();
  const [novo, setNovo] = useState('');
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingValue, setEditingValue] = useState('');

  const { data: items = [], isLoading } = useQuery({
    queryKey: ['tax', kind],
    queryFn: () => listTaxonomy(kind),
  });

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ['tax', kind] });
  }
  function onError(err: unknown) {
    notifications.show({ color: 'red', message: apiErrorMessage(err) });
  }

  const add = useMutation({
    mutationFn: (nome: string) => createTaxonomy(kind, nome),
    onSuccess: () => {
      setNovo('');
      invalidate();
    },
    onError,
  });

  const rename = useMutation({
    mutationFn: ({ id, nome }: { id: number; nome: string }) => updateTaxonomy(kind, id, nome),
    onSuccess: () => {
      setEditingId(null);
      invalidate();
    },
    onError,
  });

  const remove = useMutation({
    mutationFn: (id: number) => deleteTaxonomy(kind, id),
    onSuccess: invalidate,
    onError,
  });

  function confirmRemove(item: NamedRef) {
    modals.openConfirmModal({
      title: 'Excluir',
      children: <Text size="sm">Excluir “{item.nome}”?</Text>,
      labels: { confirm: 'Excluir', cancel: 'Cancelar' },
      confirmProps: { color: 'red' },
      onConfirm: () => remove.mutate(item.id),
    });
  }

  return (
    <Stack>
      <Group align="flex-end">
        <TextInput
          label="Adicionar"
          placeholder="Nome"
          value={novo}
          onChange={(e) => setNovo(e.currentTarget.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && novo.trim()) add.mutate(novo.trim());
          }}
          style={{ flex: 1 }}
        />
        <Button
          leftSection={<IconPlus size={16} />}
          disabled={!novo.trim()}
          loading={add.isPending}
          onClick={() => add.mutate(novo.trim())}
        >
          Adicionar
        </Button>
      </Group>

      <Table striped>
        <Table.Tbody>
          {isLoading ? (
            <Table.Tr>
              <Table.Td>
                <Text c="dimmed" py="sm">
                  Carregando…
                </Text>
              </Table.Td>
            </Table.Tr>
          ) : items.length === 0 ? (
            <Table.Tr>
              <Table.Td>
                <Text c="dimmed" py="sm">
                  Nenhum registro.
                </Text>
              </Table.Td>
            </Table.Tr>
          ) : (
            items.map((it) => (
              <Table.Tr key={it.id}>
                <Table.Td>
                  {editingId === it.id ? (
                    <Group gap={6}>
                      <TextInput
                        value={editingValue}
                        onChange={(e) => setEditingValue(e.currentTarget.value)}
                        size="xs"
                        style={{ flex: 1 }}
                        autoFocus
                      />
                      <ActionIcon
                        color="green"
                        variant="subtle"
                        onClick={() =>
                          editingValue.trim() &&
                          rename.mutate({ id: it.id, nome: editingValue.trim() })
                        }
                        aria-label="Salvar"
                      >
                        <IconCheck size={16} />
                      </ActionIcon>
                      <ActionIcon
                        color="gray"
                        variant="subtle"
                        onClick={() => setEditingId(null)}
                        aria-label="Cancelar"
                      >
                        <IconX size={16} />
                      </ActionIcon>
                    </Group>
                  ) : (
                    <Group justify="space-between">
                      <Text>{it.nome}</Text>
                      <Group gap={4}>
                        <ActionIcon
                          variant="subtle"
                          aria-label="Renomear"
                          onClick={() => {
                            setEditingId(it.id);
                            setEditingValue(it.nome);
                          }}
                        >
                          <IconEdit size={16} />
                        </ActionIcon>
                        <ActionIcon
                          variant="subtle"
                          color="red"
                          aria-label="Excluir"
                          onClick={() => confirmRemove(it)}
                        >
                          <IconTrash size={16} />
                        </ActionIcon>
                      </Group>
                    </Group>
                  )}
                </Table.Td>
              </Table.Tr>
            ))
          )}
        </Table.Tbody>
      </Table>
    </Stack>
  );
}

export function AdminTaxonomyPage() {
  return (
    <Stack gap="lg">
      <Title order={2}>Gêneros, plataformas e empresas</Title>
      <Card withBorder radius="md" p="lg">
        <Tabs defaultValue="genres">
          <Tabs.List mb="md">
            {KINDS.map((k) => (
              <Tabs.Tab key={k.value} value={k.value}>
                {k.label}
              </Tabs.Tab>
            ))}
          </Tabs.List>
          {KINDS.map((k) => (
            <Tabs.Panel key={k.value} value={k.value}>
              <TaxonomyManager kind={k.value} />
            </Tabs.Panel>
          ))}
        </Tabs>
      </Card>
    </Stack>
  );
}
