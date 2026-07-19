import { createTheme, type MantineColorsTuple } from '@mantine/core';

// Paleta da marca GameCheck — derivada do gradiente violeta→azul da logo.
const brand: MantineColorsTuple = [
  '#EFE9FE',
  '#DCCFFC',
  '#BDA4FB',
  '#9B75FA',
  '#7C4AF9',
  '#6227F9',
  '#4D09F9',
  '#4309D7',
  '#3C0EB1',
  '#34108E',
];

// Escala "dark" retintada para azul-marinho, casando com o card da logo.
// Mantém a mesma luminância do padrão do Mantine (contraste preservado).
// dark[7] = fundo do app · dark[6] = superfícies/cards.
const dark: MantineColorsTuple = [
  '#BDBEC9',
  '#A0A2B1',
  '#87899F',
  '#515571',
  '#2D304A',
  '#21243E',
  '#1A1D36',
  '#111327',
  '#0C0E1F',
  '#090B1A',
];

export const theme = createTheme({
  primaryColor: 'brand',
  primaryShade: { light: 6, dark: 6 },
  defaultRadius: 'md',
  colors: { brand, dark },
  // Gradiente padrão espelha a logo (violeta do "G" → azul da seta).
  defaultGradient: { from: '#7137F3', to: '#1584FD', deg: 135 },
});
