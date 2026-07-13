import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Anchor,
  Button,
  Card,
  Center,
  Divider,
  PasswordInput,
  Stack,
  Text,
  TextInput,
  Title,
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { useAuth } from '../../auth/AuthContext';
import { apiErrorMessage } from '../../api/client';
import { SteamLoginButton } from '../../components/SteamLoginButton';

export function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const form = useForm({
    initialValues: { nome: '', email: '', password: '', confirm: '' },
    validate: {
      nome: (v) => (v.trim().length >= 2 ? null : 'Informe seu nome'),
      email: (v) => (/^\S+@\S+$/.test(v) ? null : 'E-mail inválido'),
      password: (v) => (v.length >= 8 ? null : 'Mínimo de 8 caracteres'),
      confirm: (v, values) => (v === values.password ? null : 'As senhas não conferem'),
    },
  });

  async function handleSubmit(values: typeof form.values) {
    setLoading(true);
    setError(null);
    try {
      await register({ nome: values.nome, email: values.email, password: values.password });
      navigate('/', { replace: true });
    } catch (err) {
      setError(apiErrorMessage(err, 'Não foi possível criar a conta.'));
    } finally {
      setLoading(false);
    }
  }

  return (
    <Center>
      <Card withBorder radius="md" p="xl" w={420} mt="xl">
        <Title order={2} ta="center" mb="lg">
          Criar conta
        </Title>
        <form onSubmit={form.onSubmit(handleSubmit)}>
          <Stack>
            <TextInput label="Nome" {...form.getInputProps('nome')} />
            <TextInput
              label="E-mail"
              placeholder="voce@exemplo.com"
              {...form.getInputProps('email')}
            />
            <PasswordInput label="Senha" {...form.getInputProps('password')} />
            <PasswordInput label="Confirmar senha" {...form.getInputProps('confirm')} />
            {error && (
              <Text c="red" size="sm">
                {error}
              </Text>
            )}
            <Button type="submit" loading={loading} fullWidth>
              Criar conta
            </Button>
            <Divider label="ou" labelPosition="center" />
            <SteamLoginButton label="Entrar com Steam" />
            <Text size="xs" ta="center" c="dimmed">
              O login por Steam funciona para contas que já vincularam a Steam pelo perfil.
            </Text>
            <Text size="sm" ta="center" c="dimmed">
              Já tem conta?{' '}
              <Anchor component={Link} to="/login">
                Entrar
              </Anchor>
            </Text>
          </Stack>
        </form>
      </Card>
    </Center>
  );
}
