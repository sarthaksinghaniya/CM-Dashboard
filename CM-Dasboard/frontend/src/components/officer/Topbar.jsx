import React from 'react';
import { Search, Bell, User, Menu } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const Topbar = () => {
  const { user } = useAuth();

  return (
    <header className="h-16 bg-white/70 backdrop-blur-md border-b border-slate-200/60 flex items-center justify-between px-6 shrink-0 shadow-[0_2px_10px_rgb(0,0,0,0.01)] z-20 sticky top-0">
      
      {/* Mobile Menu Button (Visible only on mobile) */}
      <button className="md:hidden mr-4 p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors">
        <Menu className="w-6 h-6" />
      </button>

      {/* Search Section */}
      <div className="flex-1 max-w-md hidden sm:block">
        <div className="relative group">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 group-focus-within:text-blue-500 transition-colors" />
          <input
            type="text"
            placeholder="Search complaints, districts, or IDs..."
            className="w-full bg-white hover:bg-slate-50 border border-slate-200/60 rounded-xl pl-10 pr-4 py-2 text-sm text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-4 focus:ring-blue-500/10 focus:border-blue-400 transition-all duration-300 shadow-sm"
          />
        </div>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-5 ml-auto sm:ml-4">
        <button className="relative p-2 text-slate-400 hover:text-slate-600 hover:bg-white rounded-full transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 shadow-sm border border-transparent hover:border-slate-200/60">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-rose-500 rounded-full border-2 border-white"></span>
        </button>

        <div className="h-6 w-px bg-slate-200 hidden sm:block"></div>

        <button className="flex items-center gap-3 p-1 pr-3 rounded-full hover:bg-white border border-transparent hover:border-slate-200/60 transition-all duration-200 group focus:outline-none hover:shadow-sm">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-100 to-indigo-50 flex items-center justify-center text-blue-600 group-hover:from-blue-500 group-hover:to-indigo-500 group-hover:text-white transition-all shadow-sm">
            <User className="w-4 h-4" />
          </div>
          <div className="hidden md:block text-left">
            <p className="text-sm font-bold text-slate-700 leading-tight group-hover:text-blue-600 transition-colors">
              {user?.name || 'Loading...'}
            </p>
            <p className="text-[11px] font-semibold text-slate-500 leading-tight capitalize">
              {user?.role || 'Guest'}
            </p>
          </div>
        </button>
      </div>
    </header>
  );
};

export default Topbar;
