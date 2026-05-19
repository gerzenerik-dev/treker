import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
} from 'recharts';
import type { BalanceSummary } from '../types';

const PIE_COLORS = ['#6366f1', '#8b5cf6', '#a78bfa', '#7c3aed', '#4f46e5', '#c4b5fd'];

interface Props {
  balance: BalanceSummary | undefined;
  loading: boolean;
}

export default function SpendingChart({ balance, loading }: Props) {
  if (loading) {
    return (
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6 animate-pulse">
        <div className="h-5 bg-slate-100 rounded w-40 mb-6" />
        <div className="h-56 bg-slate-50 rounded-xl" />
      </div>
    );
  }

  if (!balance || balance.by_category.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6 flex flex-col items-center justify-center h-72">
        <div className="w-16 h-16 bg-slate-50 rounded-2xl flex items-center justify-center mb-4 text-3xl">
          📊
        </div>
        <p className="font-semibold text-slate-900">No data yet</p>
        <p className="text-slate-500 text-sm mt-1 text-center">
          Add categorised transactions to see your spending breakdown
        </p>
      </div>
    );
  }

  const expenses = balance.by_category
    .filter((c) => c.type === 'expense')
    .map((c) => ({ name: c.category_name, value: parseFloat(c.total) }));

  const incomes = balance.by_category
    .filter((c) => c.type === 'income')
    .map((c) => ({ name: c.category_name, value: parseFloat(c.total) }));

  const hasBoth = expenses.length > 0 && incomes.length > 0;

  if (hasBoth) {
    const allNames = [...new Set([...expenses.map((e) => e.name), ...incomes.map((i) => i.name)])];
    const barData = allNames.map((name) => ({
      name,
      Income: incomes.find((i) => i.name === name)?.value ?? 0,
      Expenses: expenses.find((e) => e.name === name)?.value ?? 0,
    }));

    return (
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
        <h3 className="font-semibold text-slate-900 mb-5">Income vs Expenses by Category</h3>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={barData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
            <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
            <Tooltip
              formatter={(v: number) => [`$${v.toFixed(2)}`, '']}
              contentStyle={{ borderRadius: '12px', border: '1px solid #e2e8f0', fontSize: 12 }}
            />
            <Legend wrapperStyle={{ fontSize: 12, paddingTop: 12 }} />
            <Bar dataKey="Income" fill="#10b981" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Expenses" fill="#f43f5e" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  const pieData = expenses.length > 0 ? expenses : incomes;
  const isExpense = expenses.length > 0;

  return (
    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
      <h3 className="font-semibold text-slate-900 mb-5">
        {isExpense ? 'Expense Breakdown' : 'Income Breakdown'}
      </h3>
      <div className="flex items-center gap-6">
        <ResponsiveContainer width="55%" height={200}>
          <PieChart>
            <Pie
              data={pieData}
              cx="50%"
              cy="50%"
              innerRadius={52}
              outerRadius={88}
              dataKey="value"
              paddingAngle={3}
              strokeWidth={0}
            >
              {pieData.map((_, i) => (
                <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              formatter={(v: number) => [`$${v.toFixed(2)}`, '']}
              contentStyle={{ borderRadius: '10px', border: '1px solid #e2e8f0', fontSize: 12 }}
            />
          </PieChart>
        </ResponsiveContainer>

        <div className="flex-1 space-y-2.5 min-w-0">
          {pieData.map((item, i) => {
            const total = pieData.reduce((s, d) => s + d.value, 0);
            const pct = total > 0 ? ((item.value / total) * 100).toFixed(0) : '0';
            return (
              <div key={item.name} className="flex items-center gap-2.5">
                <div
                  className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                  style={{ backgroundColor: PIE_COLORS[i % PIE_COLORS.length] }}
                />
                <span className="text-sm text-slate-600 truncate flex-1">{item.name}</span>
                <span className="text-xs text-slate-400 flex-shrink-0">{pct}%</span>
                <span className="text-sm font-semibold text-slate-900 flex-shrink-0">
                  ${item.value.toFixed(0)}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
