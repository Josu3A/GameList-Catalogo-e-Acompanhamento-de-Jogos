// Monta a rota do perfil mostrando o NOME do usuário na URL.
// O id (usado pelo backend em /api/profiles/{id}/) viaja pelo `state` do
// React Router — nunca aparece na URL nem em qualquer lugar visível do front.

export interface ProfileTarget {
  id: number;
  nome: string;
}

/** "João da Silva" -> "joao-da-silva" (sem acentos, minúsculo, hifenizado). */
export function slugifyNome(nome: string): string {
  const slug = nome
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '') // remove marcas de acento
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
  return slug || 'usuario';
}

/** Caminho do perfil: /users/<nome-slug> (sem o id). */
export function profilePath(nome: string): string {
  return `/users/${slugifyNome(nome)}`;
}

/**
 * Props prontas para <Link {...profileLink(u)} />: `to` com o nome e
 * `state.userId` com o id que o ProfilePage usa para consultar a API.
 */
export function profileLink(u: ProfileTarget): {
  to: string;
  state: { userId: number };
} {
  return { to: profilePath(u.nome), state: { userId: u.id } };
}
