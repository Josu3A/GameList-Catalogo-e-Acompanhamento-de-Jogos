import { api } from './client';
import type { Profile } from '../types';

export async function getProfile(userId: number): Promise<Profile> {
  const { data } = await api.get<Profile>(`/api/profiles/${userId}/`);
  return data;
}
