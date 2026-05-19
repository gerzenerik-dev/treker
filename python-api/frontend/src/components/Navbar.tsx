import { LogOut, TrendingUp, Bell } from 'lucide-react';
import type { User } from '../types';
import { useAuth } from '../context/AuthContext';

export default function Navbar({ user }: { user: User }) {
  const { logout } = useAuth();

  return (
    <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-slate-200/60">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-indigo-600 to-violet-600 rounded-lg flex items-center justify-center shadow-sm">
              <TrendingUp className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-slate-900 text-lg tracking-tight">Treker</span>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right hidden sm:block">
              <p className="text-sm font-semibold text-slate-900 leading-none">{user.username}</p>
              <p className="text-xs text-slate-500 mt-0.5">{user.email}</p>
            </div>

            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-500 to-violet-500 flex items-center justify-center text-white font-bold text-sm shadow-sm">
              {user.username[0].toUpperCase()}
            </div>

            <button
              onClick={logout}
              title="Sign out"
              className="flex items-center gap-1.5 px-3 py-2 text-sm text-slate-500 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-colors"
            >
              <LogOut className="w-4 h-4" />
              <span className="hidden sm:inline font-medium">Sign out</span>
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
