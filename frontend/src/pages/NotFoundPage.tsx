import { Link } from 'react-router-dom';
import { Button, Center, Stack, Text, Title } from '@mantine/core';

export function NotFoundPage() {
  return (
    <Center>
      <Stack align="center" py="xl" gap="sm">
        <Title order={1}>404</Title>
        <Text c="dimmed">Página não encontrada.</Text>
        <Button component={Link} to="/" mt="sm">
          Voltar ao início
        </Button>
      </Stack>
    </Center>
  );
}
