import { useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { Trash2, ArrowUpCircle, ArrowDownCircle, Receipt } from 'lucide-react';
import type { Transaction, Category } from '../types';
import { deleteTransaction } from '../api/transactions';

interface Props {
  transactions: Transaction[];
  loading: boolean;
  categories: Category[];
}

export default function TransactionList({ transactions, loading, categories }: Props) {
  const qc = useQueryClient();

  const deleteMutation = useMutation({
    mutationFn: deleteTransaction,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['transactions'] });
      qc.invalidateQueries({ queryKey: ['balance'] });
      toast.success('Transaction deleted');
    },
    onError: () => toast.error('Failed to delete'),
  });

  const getCategoryName = (id: number | null) =>
    id ? (categories.find((c) => c.id === id)?.name ?? null) : null;

  const formatDate = (dateStr: string) =>
    new Date(dateStr + 'T00:00:00').toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });

  const formatAmount = (amount: string) =>
    parseFloat(amount).toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });

  return (
    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm">
      <div className="flex items-center justify-between px-6 py-5 border-b border-slate-50">
        <div className="flex items-center gap-2.5">
          <Receipt className="w-4 h-4 text-slate-400" />
          <h3 className="font-semibold text-slate-900">Recent Transactions</h3>
        </div>
        <span className="text-xs font-medium text-slate-400 bg-slate-50 px-2.5 py-1 rounded-full">
          {transactions.length} entries
        </span>
      </div>

      <div className="p-4">
        {loading ? (
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex items-center gap-4 p-3 animate-pulse">
                <div className="w-10 h-10 bg-slate-100 rounded-xl flex-shrink-0" />
                <div className="flex-1 space-y-2">
                  <div className="h-3.5 bg-slate-100 rounded w-1/3" />
                  <div className="h-3 bg-slate-100 rounded w-1/5" />
                </div>
                <div className="h-4 bg-slate-100 rounded w-16" />
              </div>
            ))}
          </div>
        ) : transactions.length === 0 ? (
          <div className="text-center py-14">
            <div className="w-16 h-16 bg-slate-50 rounded-2xl flex items-center justify-center mx-auto mb-4 text-3xl">
              💸
            </div>
            <p className="font-semibold text-slate-900">No transactions yet</p>
            <p className="text-slate-500 text-sm mt-1.5">
              Use the form above to add your first transaction
            </p>
          </div>
        ) : (
          <div className="space-y-1">
            {transactions.map((tx) => {
              const catName = getCategoryName(tx.category_id);
              const isIncome = tx.type === 'income';

              return (
                <div
                  key={tx.id}
                  className="group flex items-center gap-3 p-3 rounded-xl hover:bg-slate-50 transition-colors"
                >
                  {/* Icon */}
                  <div
                    className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
                      isIncome ? 'bg-emerald-50' : 'bg-rose-50'
                    }`}
                  >
                    {isIncome ? (
                      <ArrowUpCircle className="w-5 h-5 text-emerald-500" />
                    ) : (
                      <ArrowDownCircle className="w-5 h-5 text-rose-500" />
                    )}
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-900 truncate">
                      {tx.description || catName || (isIncome ? 'Income' : 'Expense')}
                    </p>
                    <div className="flex items-center gap-2 mt-0.5">
                      {catName && (
                        <span className="text-xs text-indigo-600 font-medium bg-indigo-50 px-1.5 py-0.5 rounded-md">
                          {catName}
                        </span>
                      )}
                      <span className="text-xs text-slate-400">{formatDate(tx.date)}</span>
                    </div>
                  </div>

                  {/* Amount + delete */}
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <span
                      className={`text-sm font-bold tabular-nums ${
                        isIncome ? 'text-emerald-600' : 'text-rose-600'
                      }`}
                    >
                      {isIncome ? '+' : '-'}${formatAmount(tx.amount)}
                    </span>
                    <button
                      onClick={() => {
                        if (window.confirm('Delete this transaction?')) {
                          deleteMutation.mutate(tx.id);
                        }
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1.5 text-slate-300 hover:text-rose-500 hover:bg-rose-50 rounded-lg transition-all"
                      title="Delete transaction"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
