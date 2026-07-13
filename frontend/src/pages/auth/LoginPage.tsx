import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
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

interface LocationState {
  from?: { pathname?: string };
}

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const from = (location.state as LocationState | null)?.from?.pathname ?? '/';

  const form = useForm({
    initialValues: { email: '', password: '' },
    validate: {
      email: (v) => (/^\S+@\S+$/.test(v) ? null : 'E-mail inválido'),
      password: (v) => (v.length ? null : 'Informe a senha'),
    },
  });

  async function handleSubmit(values: typeof form.values) {
    setLoading(true);
    setError(null);
    try {
      await login(values);
      navigate(from, { replace: true });
    } catch (err) {
      setError(apiErrorMessage(err, 'Não foi possível entrar.'));
    } finally {
      setLoading(false);
    }
  }

  return (
    <Center>
      <Card withBorder radius="md" p="xl" w={400} mt="xl">
        <Title order={2} ta="center" mb="lg">
          Entrar
        </Title>
        <form onSubmit={form.onSubmit(handleSubmit)}>
          <Stack>
            <TextInput
              label="E-mail"
              placeholder="voce@exemplo.com"
              {...form.getInputProps('email')}
            />
            <PasswordInput label="Senha" {...form.getInputProps('password')} />
            {error && (
              <Text c="red" size="sm">
                {error}
              </Text>
            )}
            <Button type="submit" loading={loading} fullWidth>
              Entrar
            </Button>
            <Divider label="ou" labelPosition="center" />
            <SteamLoginButton />
            <Text size="sm" ta="center" c="dimmed">
              Não tem conta?{' '}
              <Anchor component={Link} to="/register">
                Criar conta
              </Anchor>
            </Text>
          </Stack>
        </form>
      </Card>
    </Center>
  );
}
