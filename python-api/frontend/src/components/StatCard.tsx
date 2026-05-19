import { TrendingUp, TrendingDown, Wallet } from 'lucide-react';

interface StatCardProps {
  label: string;
  value: number;
  variant: 'balance' | 'negative' | 'income' | 'expense';
  loading?: boolean;
}

const CONFIGS = {
  balance: {
    gradient: 'bg-gradient-to-br from-indigo-500 to-violet-600',
    icon: Wallet,
    textColor: 'text-white',
    labelColor: 'text-indigo-100',
    iconBg: 'bg-white/20',
    iconColor: 'text-white',
  },
  negative: {
    gradient: 'bg-gradient-to-br from-rose-500 to-rose-600',
    icon: TrendingDown,
    textColor: 'text-white',
    labelColor: 'text-rose-100',
    iconBg: 'bg-white/20',
    iconColor: 'text-white',
  },
  income: {
    gradient: 'bg-white border border-slate-100',
    icon: TrendingUp,
    textColor: 'text-emerald-600',
    labelColor: 'text-slate-500',
    iconBg: 'bg-emerald-50',
    iconColor: 'text-emerald-500',
  },
  expense: {
    gradient: 'bg-white border border-slate-100',
    icon: TrendingDown,
    textColor: 'text-rose-600',
    labelColor: 'text-slate-500',
    iconBg: 'bg-rose-50',
    iconColor: 'text-rose-500',
  },
};

export default function StatCard({ label, value, variant, loading }: StatCardProps) {
  const c = CONFIGS[variant];
  const Icon = c.icon;
  const formatted = `$${Math.abs(value).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;

  if (loading) {
    return (
      <div className={`rounded-2xl p-6 ${c.gradient} shadow-sm animate-pulse`}>
        <div className="h-3.5 bg-white/30 rounded w-24 mb-4" />
        <div className="h-8 bg-white/30 rounded w-36" />
      </div>
    );
  }

  return (
    <div className={`rounded-2xl p-6 ${c.gradient} shadow-sm hover:-translate-y-0.5 transition-transform duration-200`}>
      <div className="flex items-start justify-between mb-4">
        <p className={`text-sm font-medium ${c.labelColor}`}>{label}</p>
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${c.iconBg}`}>
          <Icon className={`w-5 h-5 ${c.iconColor}`} />
        </div>
      </div>
      <p className={`text-3xl font-bold tracking-tight ${c.textColor}`}>
        {value < 0 ? '-' : ''}{formatted}
      </p>
    </div>
  );
}
