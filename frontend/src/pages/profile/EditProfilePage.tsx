import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Avatar,
  Button,
  Card,
  FileButton,
  Group,
  Stack,
  Switch,
  Text,
  Textarea,
  TextInput,
  Title,
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { updateMe } from '../../api/auth';
import { apiErrorMessage } from '../../api/client';
import { useAuth } from '../../auth/AuthContext';
import { profilePath } from '../../lib/profileUrl';
import { SteamAccountCard } from '../../components/SteamAccountCard';

// Limites do upload de avatar — espelham a validação do backend.
const MAX_AVATAR_MB = 2;
const MAX_AVATAR_BYTES = MAX_AVATAR_MB * 1024 * 1024;
const AVATAR_ACCEPT = 'image/jpeg,image/png,image/webp,image/gif';

export function EditProfilePage() {
  const { user, refresh } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  // Estado do avatar: arquivo novo escolhido, flag de remoção e URL de preview local.
  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [removeAvatar, setRemoveAvatar] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  // Libera o object URL do preview quando troca/desmonta (evita vazamento).
  useEffect(() => {
    if (!avatarFile) {
      setPreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(avatarFile);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [avatarFile]);

  const form = useForm({
    initialValues: {
      nome: user?.nome ?? '',
      email: user?.email ?? '',
      bio: user?.bio ?? '',
      perfil_publico: user?.perfil_publico ?? true,
    },
    validate: {
      nome: (v) => (v.trim().length >= 2 ? null : 'Informe seu nome'),
      email: (v) => (/^\S+@\S+$/.test(v) ? null : 'E-mail inválido'),
    },
  });

  function handlePickAvatar(file: File | null) {
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      notifications.show({ color: 'red', message: 'Selecione um arquivo de imagem.' });
      return;
    }
    if (file.size > MAX_AVATAR_BYTES) {
      notifications.show({
        color: 'red',
        message: `A imagem deve ter no máximo ${MAX_AVATAR_MB} MB.`,
      });
      return;
    }
    setAvatarFile(file);
    setRemoveAvatar(false);
  }

  function handleRemoveAvatar() {
    setAvatarFile(null);
    setRemoveAvatar(true);
  }

  // O que mostrar no preview: foto nova > (removida ? vazio : avatar atual).
  const shownAvatar = previewUrl ?? (removeAvatar ? undefined : user?.avatar_url ?? undefined);
  const hasAvatar = Boolean(previewUrl) || (!removeAvatar && Boolean(user?.avatar_url));

  async function handleSubmit(values: typeof form.values) {
    setLoading(true);
    try {
      await updateMe({
        nome: values.nome,
        email: values.email,
        bio: values.bio.trim() ? values.bio : null,
        perfil_publico: values.perfil_publico,
        avatarFile,
        removeAvatar,
      });
      await refresh();
      notifications.show({ color: 'green', message: 'Perfil atualizado.' });
      if (user) navigate(profilePath(values.nome), { state: { userId: user.id } });
    } catch (err) {
      notifications.show({ color: 'red', message: apiErrorMessage(err) });
    } finally {
      setLoading(false);
    }
  }

  return (
    <Stack gap="lg" maw={560}>
      <Title order={2}>Editar perfil</Title>
      <Card withBorder radius="md" p="lg">
        <form onSubmit={form.onSubmit(handleSubmit)}>
          <Stack>
            <div>
              <Text size="sm" fw={500} mb={6}>
                Foto de perfil
              </Text>
              <Group>
                <Avatar src={shownAvatar} size={80} radius="xl">
                  {form.values.nome.slice(0, 1).toUpperCase()}
                </Avatar>
                <Stack gap={6}>
                  <Group gap="xs">
                    <FileButton onChange={handlePickAvatar} accept={AVATAR_ACCEPT}>
                      {(props) => (
                        <Button {...props} variant="default" size="xs">
                          {hasAvatar ? 'Trocar foto' : 'Enviar foto'}
                        </Button>
                      )}
                    </FileButton>
                    {hasAvatar && (
                      <Button variant="subtle" color="red" size="xs" onClick={handleRemoveAvatar}>
                        Remover
                      </Button>
                    )}
                  </Group>
                  <Text size="xs" c="dimmed">
                    JPG, PNG, WEBP ou GIF · até {MAX_AVATAR_MB} MB
                  </Text>
                </Stack>
              </Group>
            </div>
            <TextInput label="Nome" {...form.getInputProps('nome')} />
            <TextInput label="E-mail" {...form.getInputProps('email')} />
            <Textarea label="Bio" autosize minRows={3} {...form.getInputProps('bio')} />
            <Switch
              label="Perfil público"
              description="Se desligado, seu perfil não aparece para outros usuários."
              checked={form.values.perfil_publico}
              {...form.getInputProps('perfil_publico', { type: 'checkbox' })}
            />
            <Group justify="flex-end" mt="sm">
              <Button type="submit" loading={loading}>
                Salvar
              </Button>
            </Group>
          </Stack>
        </form>
      </Card>
      <SteamAccountCard />
      {!user && <Text c="dimmed">Carregando…</Text>}
    </Stack>
  );
}
