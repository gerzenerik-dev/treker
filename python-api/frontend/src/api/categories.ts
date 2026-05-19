import { client } from './client';
import type { Category } from '../types';

export async function getCategories(type?: 'income' | 'expense'): Promise<Category[]> {
  const params = type ? { type } : {};
  const { data } = await client.get<Category[]>('/categories/', { params });
  return data;
}

export async function createCategory(name: string, type: 'income' | 'expense'): Promise<Category> {
  const { data } = await client.post<Category>('/categories/', { name, type });
  return data;
}

export async function deleteCategory(id: number): Promise<void> {
  await client.delete(`/categories/${id}`);
}
