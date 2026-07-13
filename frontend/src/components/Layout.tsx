import { AppShell, Container } from '@mantine/core';
import { Outlet } from 'react-router-dom';
import { Navbar } from './Navbar';
import { useSteamNotice } from '../lib/useSteamNotice';

export function Layout() {
  useSteamNotice();
  return (
    <AppShell header={{ height: 60 }} padding="md">
      <AppShell.Header>
        <Navbar />
      </AppShell.Header>
      <AppShell.Main>
        <Container size="lg" py="md">
          <Outlet />
        </Container>
      </AppShell.Main>
    </AppShell>
  );
}
