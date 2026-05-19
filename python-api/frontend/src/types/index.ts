export type TransactionType = 'income' | 'expense';

export interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
}

export interface Category {
  id: number;
  user_id: number;
  name: string;
  type: TransactionType;
  created_at: string;
}

export interface Transaction {
  id: number;
  user_id: number;
  category_id: number | null;
  type: TransactionType;
  amount: string;
  description: string | null;
  date: string;
  created_at: string;
}

export interface CategoryBreakdown {
  category_id: number;
  category_name: string;
  type: TransactionType;
  total: string;
}

export interface BalanceSummary {
  income: string;
  expenses: string;
  balance: string;
  by_category: CategoryBreakdown[];
}

export interface Token {
  access_token: string;
  token_type: string;
}
