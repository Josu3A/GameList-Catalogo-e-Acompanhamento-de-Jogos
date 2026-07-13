import { createTheme } from '@mantine/core';

// Tema base (escuro por padrão em main.tsx). Paleta/tipografia definitivas
// serão ajustadas depois — por ora usamos os tokens padrão do Mantine.
export const theme = createTheme({
  primaryColor: 'violet',
  defaultRadius: 'md',
});
