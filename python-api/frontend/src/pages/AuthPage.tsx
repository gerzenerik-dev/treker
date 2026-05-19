import { useState, type FormEvent, type ReactNode } from 'react';
import { useMutation } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { TrendingUp, Mail, Lock, User, Eye, EyeOff } from 'lucide-react';
import { login as apiLogin, register as apiRegister } from '../api/auth';
import { useAuth } from '../context/AuthContext';

type Tab = 'login' | 'register';

export default function AuthPage() {
  const [tab, setTab] = useState<Tab>('login');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const { login } = useAuth();

  const loginMutation = useMutation({
    mutationFn: () => apiLogin(username, password),
    onSuccess: async (data) => {
      await login(data.access_token);
      toast.success('Welcome back!');
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Login failed. Check your credentials.');
    },
  });

  const registerMutation = useMutation({
    mutationFn: () => apiRegister(username, email, password),
    onSuccess: async () => {
      const tokenData = await apiLogin(username, password);
      await login(tokenData.access_token);
      toast.success('Account created! Welcome to Treker 🎉');
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Registration failed.');
    },
  });

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (tab === 'login') loginMutation.mutate();
    else registerMutation.mutate();
  };

  const isLoading = loginMutation.isPending || registerMutation.isPending;

  return (
    <div className="min-h-screen flex bg-gradient-to-br from-slate-900 via-indigo-950 to-violet-950">
      {/* Left panel — branding */}
      <div className="hidden lg:flex lg:flex-1 flex-col justify-center px-16 py-12">
        <div className="flex items-center gap-3 mb-12">
          <div className="w-10 h-10 bg-gradient-to-br from-indigo-400 to-violet-400 rounded-xl flex items-center justify-center">
            <TrendingUp className="w-5 h-5 text-white" />
          </div>
          <span className="text-white font-bold text-xl">Treker</span>
        </div>

        <h1 className="text-5xl font-bold text-white leading-tight mb-6">
          Take control of your finances
        </h1>
        <p className="text-indigo-200 text-lg leading-relaxed max-w-md">
          Track income and expenses, visualise spending patterns, and stay on top of your financial health — all in one place.
        </p>

        <div className="mt-12 grid grid-cols-2 gap-4 max-w-sm">
          {[
            { icon: '💰', label: 'Track Income' },
            { icon: '📊', label: 'Visualise Spending' },
            { icon: '🏷️', label: 'Custom Categories' },
            { icon: '⚡', label: 'Real-time Balance' },
          ].map((f) => (
            <div key={f.label} className="flex items-center gap-3 text-sm text-indigo-200">
              <span className="text-lg">{f.icon}</span>
              {f.label}
            </div>
          ))}
        </div>
      </div>

      {/* Right panel — form */}
      <div className="flex-1 lg:max-w-md flex items-center justify-center p-6">
        <div className="w-full max-w-sm">
          {/* Mobile logo */}
          <div className="lg:hidden text-center mb-8">
            <div className="inline-flex items-center justify-center w-14 h-14 bg-gradient-to-br from-indigo-500 to-violet-500 rounded-2xl mb-3 shadow-lg">
              <TrendingUp className="w-7 h-7 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-white">Treker</h1>
          </div>

          <div className="bg-white rounded-3xl shadow-2xl overflow-hidden">
            {/* Tabs */}
            <div className="flex border-b border-slate-100">
              {(['login', 'register'] as Tab[]).map((t) => (
                <button
                  key={t}
                  onClick={() => setTab(t)}
                  className={`flex-1 py-4 text-sm font-semibold transition-colors ${
                    tab === t
                      ? 'text-indigo-600 border-b-2 border-indigo-600 bg-indigo-50/40'
                      : 'text-slate-500 hover:text-slate-700'
                  }`}
                >
                  {t === 'login' ? 'Sign In' : 'Create Account'}
                </button>
              ))}
            </div>

            <form onSubmit={handleSubmit} className="p-8 space-y-5">
              <Field
                icon={<User className="w-4 h-4" />}
                label="Username"
                type="text"
                value={username}
                onChange={setUsername}
                placeholder="yourname"
                required
                autoComplete="username"
              />

              {tab === 'register' && (
                <Field
                  icon={<Mail className="w-4 h-4" />}
                  label="Email"
                  type="email"
                  value={email}
                  onChange={setEmail}
                  placeholder="you@example.com"
                  required
                  autoComplete="email"
                />
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5">
                  Password
                </label>
                <div className="relative">
                  <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400">
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    required
                    autoComplete={tab === 'login' ? 'current-password' : 'new-password'}
                    className="w-full pl-10 pr-11 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition-colors"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3.5 bg-gradient-to-r from-indigo-600 to-violet-600 text-white rounded-xl font-semibold text-sm shadow-lg shadow-indigo-200 hover:shadow-xl hover:from-indigo-700 hover:to-violet-700 transition-all duration-200 disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : tab === 'login' ? (
                  'Sign In'
                ) : (
                  'Create Account'
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

function Field({
  icon,
  label,
  type,
  value,
  onChange,
  placeholder,
  required,
  autoComplete,
}: {
  icon: ReactNode;
  label: string;
  type: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  required?: boolean;
  autoComplete?: string;
}) {
  return (
    <div>
      <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5">
        {label}
      </label>
      <div className="relative">
        <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400">{icon}</div>
        <input
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          required={required}
          autoComplete={autoComplete}
          className="w-full pl-10 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition-colors"
        />
      </div>
    </div>
  );
}
