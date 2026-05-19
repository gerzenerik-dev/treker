import { client } from './client';
import type { Token, User } from '../types';

export async function login(username: string, password: string): Promise<Token> {
  const params = new URLSearchParams({ username, password });
  const { data } = await client.post<Token>('/auth/login', params);
  return data;
}

export async function register(username: string, email: string, password: string): Promise<User> {
  const { data } = await client.post<User>('/auth/register', { username, email, password });
  return data;
}

export async function getMe(): Promise<User> {
  const { data } = await client.get<User>('/users/me');
  return data;
}
