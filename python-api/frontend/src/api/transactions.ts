import { client } from './client';
import type { BalanceSummary, Transaction } from '../types';

interface CreateTransactionPayload {
  type: 'income' | 'expense';
  amount: number;
  category_id?: number;
  description?: string;
  date: string;
}

export async function getBalance(startDate?: string, endDate?: string): Promise<BalanceSummary> {
  const params: Record<string, string> = {};
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;
  const { data } = await client.get<BalanceSummary>('/transactions/balance', { params });
  return data;
}

export async function getTransactions(params?: {
  type?: string;
  category_id?: number;
  skip?: number;
  limit?: number;
  start_date?: string;
  end_date?: string;
}): Promise<Transaction[]> {
  const { data } = await client.get<Transaction[]>('/transactions/', { params });
  return data;
}

export async function createTransaction(payload: CreateTransactionPayload): Promise<Transaction> {
  const { data } = await client.post<Transaction>('/transactions/', payload);
  return data;
}

export async function deleteTransaction(id: number): Promise<void> {
  await client.delete(`/transactions/${id}`);
}
