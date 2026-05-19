import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { Plus, Tag, X } from 'lucide-react';
import { createTransaction } from '../api/transactions';
import { createCategory } from '../api/categories';
import type { Category } from '../types';

export default function AddTransactionForm({ categories }: { categories: Category[] }) {
  const qc = useQueryClient();
  const today = new Date().toISOString().split('T')[0];

  const [type, setType] = useState<'income' | 'expense'>('expense');
  const [amount, setAmount] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [description, setDescription] = useState('');
  const [date, setDate] = useState(today);
  const [newCatName, setNewCatName] = useState('');
  const [showNewCat, setShowNewCat] = useState(false);

  const filtered = categories.filter((c) => c.type === type);

  const txMutation = useMutation({
    mutationFn: () =>
      createTransaction({
        type,
        amount: parseFloat(amount),
        category_id: categoryId ? parseInt(categoryId) : undefined,
        description: description.trim() || undefined,
        date,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['transactions'] });
      qc.invalidateQueries({ queryKey: ['balance'] });
      setAmount('');
      setCategoryId('');
      setDescription('');
      setDate(today);
      toast.success(type === 'income' ? '💰 Income recorded!' : '💸 Expense recorded!');
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Failed to add transaction'),
  });

  const catMutation = useMutation({
    mutationFn: () => createCategory(newCatName.trim(), type),
    onSuccess: (cat) => {
      qc.invalidateQueries({ queryKey: ['categories'] });
      setCategoryId(String(cat.id));
      setNewCatName('');
      setShowNewCat(false);
      toast.success(`Category "${cat.name}" created`);
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || 'Failed to create category'),
  });

  const canSubmit = amount && parseFloat(amount) > 0 && !txMutation.isPending;

  return (
    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
      <h3 className="font-semibold text-slate-900 mb-5">Add Transaction</h3>

      {/* Type toggle */}
      <div className="flex rounded-xl bg-slate-100 p-1 mb-5 gap-1">
        {(['expense', 'income'] as const).map((t) => (
          <button
            key={t}
            onClick={() => {
              setType(t);
              setCategoryId('');
            }}
            className={`flex-1 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200 ${
              type === t
                ? t === 'income'
                  ? 'bg-emerald-500 text-white shadow-sm shadow-emerald-200'
                  : 'bg-rose-500 text-white shadow-sm shadow-rose-200'
                : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            {t === 'income' ? '↑ Income' : '↓ Expense'}
          </button>
        ))}
      </div>

      <div className="space-y-4">
        {/* Amount */}
        <div>
          <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5">
            Amount
          </label>
          <div className="relative">
            <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 font-medium text-sm select-none">
              $
            </span>
            <input
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="0.00"
              min="0.01"
              step="0.01"
              className="w-full pl-8 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition-colors"
            />
          </div>
        </div>

        {/* Category */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
              Category
            </label>
            <button
              onClick={() => setShowNewCat(!showNewCat)}
              className="flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-700 font-medium"
            >
              {showNewCat ? <X className="w-3 h-3" /> : <Tag className="w-3 h-3" />}
              {showNewCat ? 'Cancel' : 'New category'}
            </button>
          </div>

          {showNewCat ? (
            <div className="flex gap-2">
              <input
                value={newCatName}
                onChange={(e) => setNewCatName(e.target.value)}
                placeholder={`e.g. ${type === 'income' ? 'Salary' : 'Groceries'}`}
                onKeyDown={(e) => e.key === 'Enter' && newCatName.trim() && catMutation.mutate()}
                className="flex-1 px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400"
              />
              <button
                onClick={() => catMutation.mutate()}
                disabled={!newCatName.trim() || catMutation.isPending}
                className="px-3.5 py-2.5 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-50 transition-colors"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <select
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)}
              className="w-full px-3.5 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition-colors text-slate-700"
            >
              <option value="">— No category —</option>
              {filtered.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Description */}
        <div>
          <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5">
            Note <span className="font-normal normal-case">(optional)</span>
          </label>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What was this for?"
            className="w-full px-3.5 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition-colors"
          />
        </div>

        {/* Date */}
        <div>
          <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5">
            Date
          </label>
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            max={today}
            className="w-full px-3.5 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition-colors text-slate-700"
          />
        </div>

        {/* Submit */}
        <button
          onClick={() => txMutation.mutate()}
          disabled={!canSubmit}
          className={`w-full py-3.5 rounded-xl font-semibold text-sm transition-all duration-200 flex items-center justify-center gap-2 mt-2 ${
            type === 'income'
              ? 'bg-emerald-500 hover:bg-emerald-600 text-white shadow-lg shadow-emerald-100 hover:shadow-emerald-200'
              : 'bg-rose-500 hover:bg-rose-600 text-white shadow-lg shadow-rose-100 hover:shadow-rose-200'
          } disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none`}
        >
          {txMutation.isPending ? (
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <>
              <Plus className="w-4 h-4" />
              Add {type === 'income' ? 'Income' : 'Expense'}
            </>
          )}
        </button>
      </div>
    </div>
  );
}
