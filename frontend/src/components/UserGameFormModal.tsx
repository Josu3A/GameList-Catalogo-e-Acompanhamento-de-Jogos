import { useEffect } from 'react';
import {
  Button,
  Group,
  Modal,
  NumberInput,
  Select,
  Stack,
  Switch,
  Textarea,
} from '@mantine/core';
import { DateInput } from '@mantine/dates';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { addMyGame, updateMyGame } from '../api/library';
import { apiErrorMessage } from '../api/client';
import { STATUS_OPTIONS } from '../lib/labels';
import type { StatusLista, UserGame } from '../types';

interface Props {
  opened: boolean;
  onClose: () => void;
  /** Modo criação: id do jogo a adicionar. */
  gameId?: number;
  /** Modo edição: item existente da lista. */
  userGame?: UserGame;
  /** Título do jogo, para o cabeçalho do modal. */
  gameTitulo?: string;
}

interface FormValues {
  status: StatusLista;
  nota: number | string;
  horas_jogadas: number | string;
  platinado: boolean;
  data_inicio: Date | null;
  data_fim: Date | null;
  review: string;
}

function toDate(iso: string | null): Date | null {
  return iso ? new Date(`${iso}T00:00:00`) : null;
}

function toISO(date: Date | null): string | null {
  return date ? dayjs(date).format('YYYY-MM-DD') : null;
}

export function UserGameFormModal({ opened, onClose, gameId, userGame, gameTitulo }: Props) {
  const queryClient = useQueryClient();
  const isEdit = !!userGame;

  const form = useForm<FormValues>({
    initialValues: {
      status: 'quero_jogar',
      nota: '',
      horas_jogadas: 0,
      platinado: false,
      data_inicio: null,
      data_fim: null,
      review: '',
    },
  });

  // Reinicializa os valores sempre que o modal abre (jogo/edição pode ter mudado).
  useEffect(() => {
    if (!opened) return;
    if (userGame) {
      form.setValues({
        status: userGame.status,
        nota: userGame.nota === null ? '' : Number(userGame.nota),
        horas_jogadas: Number(userGame.horas_jogadas),
        platinado: userGame.platinado,
        data_inicio: toDate(userGame.data_inicio),
        data_fim: toDate(userGame.data_fim),
        review: userGame.review ?? '',
      });
    } else {
      form.reset();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened, userGame?.id]);

  const mutation = useMutation({
    mutationFn: async (values: FormValues) => {
      const base = {
        status: values.status,
        nota: values.nota === '' ? null : Number(values.nota),
        horas_jogadas: values.horas_jogadas === '' ? 0 : Number(values.horas_jogadas),
        platinado: values.platinado,
        data_inicio: toISO(values.data_inicio),
        data_fim: toISO(values.data_fim),
        review: values.review.trim() ? values.review : null,
      };
      if (isEdit) {
        return updateMyGame(userGame!.id, base);
      }
      return addMyGame({ game_id: gameId!, ...base });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-games'] });
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      notifications.show({
        color: 'green',
        message: isEdit ? 'Item atualizado.' : 'Jogo adicionado à sua lista.',
      });
      onClose();
    },
    onError: (err) => {
      notifications.show({ color: 'red', message: apiErrorMessage(err) });
    },
  });

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title={
        isEdit
          ? `Editar — ${userGame?.game.titulo ?? ''}`
          : `Adicionar${gameTitulo ? ` — ${gameTitulo}` : ' à minha lista'}`
      }
      centered
    >
      <form onSubmit={form.onSubmit((v) => mutation.mutate(v))}>
        <Stack>
          <Select
            label="Status"
            data={STATUS_OPTIONS}
            allowDeselect={false}
            {...form.getInputProps('status')}
          />
          <Group grow>
            <NumberInput
              label="Nota (0–10)"
              min={0}
              max={10}
              step={0.5}
              decimalScale={1}
              placeholder="Sem nota"
              {...form.getInputProps('nota')}
            />
            <NumberInput
              label="Horas jogadas"
              min={0}
              step={1}
              decimalScale={1}
              {...form.getInputProps('horas_jogadas')}
            />
          </Group>
          <Group grow>
            <DateInput
              label="Início"
              valueFormat="DD/MM/YYYY"
              clearable
              {...form.getInputProps('data_inicio')}
            />
            <DateInput
              label="Fim"
              valueFormat="DD/MM/YYYY"
              clearable
              {...form.getInputProps('data_fim')}
            />
          </Group>
          <Switch
            label="Platinado"
            checked={form.values.platinado}
            {...form.getInputProps('platinado', { type: 'checkbox' })}
          />
          <Textarea
            label="Review (opcional)"
            autosize
            minRows={3}
            {...form.getInputProps('review')}
          />
          <Group justify="flex-end" mt="sm">
            <Button variant="default" onClick={onClose}>
              Cancelar
            </Button>
            <Button type="submit" loading={mutation.isPending}>
              {isEdit ? 'Salvar' : 'Adicionar'}
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}
