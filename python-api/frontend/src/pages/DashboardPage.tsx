import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { CalendarDays } from 'lucide-react';
import { getBalance, getTransactions } from '../api/transactions';
import { getCategories } from '../api/categories';
import { useAuth } from '../context/AuthContext';
import Navbar from '../components/Navbar';
import StatCard from '../components/StatCard';
import SpendingChart from '../components/SpendingChart';
import AddTransactionForm from '../components/AddTransactionForm';
import TransactionList from '../components/TransactionList';

type DateRange = 'week' | 'month' | 'year' | 'all';

function getDateRange(range: DateRange): { start?: string; end?: string } {
  const today = new Date();
  const fmt = (d: Date) => d.toISOString().split('T')[0];
  if (range === 'all') return {};
  const start = new Date(today);
  if (range === 'week') start.setDate(today.getDate() - 7);
  else if (range === 'month') start.setMonth(today.getMonth() - 1);
  else if (range === 'year') start.setFullYear(today.getFullYear() - 1);
  return { start: fmt(start), end: fmt(today) };
}

function greeting() {
  const h = new Date().getHours();
  return h < 12 ? 'morning' : h < 17 ? 'afternoon' : 'evening';
}

const RANGE_LABELS: Record<DateRange, string> = {
  week: 'This week',
  month: 'This month',
  year: 'This year',
  all: 'All time',
};

export default function DashboardPage() {
  const { user } = useAuth();
  const [dateRange, setDateRange] = useState<DateRange>('month');
  const { start, end } = getDateRange(dateRange);

  const { data: balance, isLoading: balanceLoading } = useQuery({
    queryKey: ['balance', dateRange],
    queryFn: () => getBalance(start, end),
  });

  const { data: transactions, isLoading: txLoading } = useQuery({
    queryKey: ['transactions', dateRange],
    queryFn: () =>
      getTransactions({ limit: 50, start_date: start, end_date: end }),
  });

  const { data: categories = [] } = useQuery({
    queryKey: ['categories'],
    queryFn: () => getCategories(),
  });

  const income = parseFloat(balance?.income ?? '0');
  const expenses = parseFloat(balance?.expenses ?? '0');
  const netBalance = parseFloat(balance?.balance ?? '0');

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-indigo-50/40">
      <Navbar user={user!} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header row */}
        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-8">
          <div>
            <h2 className="text-2xl font-bold text-slate-900">
              Good {greeting()}, {user?.username} 👋
            </h2>
            <p className="text-slate-500 mt-1">
              {new Date().toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })}
            </p>
          </div>

          {/* Date range filter */}
          <div className="flex items-center gap-2 bg-white rounded-xl border border-slate-200 p-1 shadow-sm">
            <CalendarDays className="w-4 h-4 text-slate-400 ml-2 hidden sm:block" />
            {(Object.keys(RANGE_LABELS) as DateRange[]).map((r) => (
              <button
                key={r}
                onClick={() => setDateRange(r)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                  dateRange === r
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                {RANGE_LABELS[r]}
              </button>
            ))}
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <StatCard
            label="Net Balance"
            value={netBalance}
            variant={netBalance >= 0 ? 'balance' : 'negative'}
            loading={balanceLoading}
          />
          <StatCard label="Total Income" value={income} variant="income" loading={balanceLoading} />
          <StatCard label="Total Expenses" value={expenses} variant="expense" loading={balanceLoading} />
        </div>

        {/* Chart + Form grid */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 mb-6">
          <div className="lg:col-span-3">
            <SpendingChart balance={balance} loading={balanceLoading} />
          </div>
          <div className="lg:col-span-2">
            <AddTransactionForm categories={categories} />
          </div>
        </div>

        {/* Transaction list */}
        <TransactionList
          transactions={transactions ?? []}
          loading={txLoading}
          categories={categories}
        />
      </main>
    </div>
  );
}
