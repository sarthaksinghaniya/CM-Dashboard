import React from 'react';
import { Search, Bell, User } from 'lucide-react';

const Topbar = () => {
  return (
    <header className="h-16 bg-white border-b border-slate-200/60 flex items-center justify-between px-6 shrink-0 shadow-[0_2px_10px_rgb(0,0,0,0.01)] z-10 sticky top-0">
      
      {/* Search Section */}
      <div className="flex-1 max-w-md">
        <div className="relative group">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 group-focus-within:text-indigo-500 transition-colors" />
          <input
            type="text"
            placeholder="Search complaints, districts, or IDs..."
            className="w-full bg-slate-50/50 hover:bg-slate-50 border border-slate-200/60 rounded-xl pl-10 pr-4 py-2 text-sm text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-400 focus:bg-white transition-all duration-300 shadow-sm"
          />
        </div>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-5 ml-4">
        <button className="relative p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-full transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-2 w-2 h-2 bg-rose-500 rounded-full border-2 border-white ring-1 ring-white"></span>
        </button>

        <div className="h-6 w-px bg-slate-200"></div>

        <button className="flex items-center gap-3 p-1 pr-3 rounded-full hover:bg-slate-50 border border-transparent hover:border-slate-200 transition-all duration-200 group focus:outline-none">
          <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 group-hover:bg-indigo-500 group-hover:text-white transition-colors">
            <User className="w-4 h-4" />
          </div>
          <div className="hidden md:block text-left">
            <p className="text-sm font-bold text-slate-700 leading-tight">Admin User</p>
            <p className="text-[11px] font-semibold text-slate-500 leading-tight">Super Admin</p>
          </div>
        </button>
      </div>
    </header>
  );
};

export default Topbar;
