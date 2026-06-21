import React from 'react';
import { NavLink } from 'react-router-dom';
import { motion } from 'framer-motion';
import { LayoutDashboard, FileText, Search, MessageSquare, Settings, LogOut, ShieldAlert } from 'lucide-react';

const Sidebar = () => {
  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard, end: true },
    { name: 'Submit Complaint', path: '/submit', icon: FileText, end: false },
    { name: 'Track Status', path: '/track', icon: Search, end: false },
    { name: 'Feedback', path: '/feedback', icon: MessageSquare, end: false },
  ];

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 text-slate-300 flex flex-col h-full shrink-0 transition-all duration-300 shadow-xl hidden md:flex">
      <div className="h-16 flex items-center px-6 border-b border-white/5">
        <div className="flex items-center gap-3 text-white w-full group cursor-pointer">
          <div className="w-9 h-9 bg-gradient-to-br from-indigo-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/20 group-hover:shadow-indigo-500/40 transition-shadow">
            <ShieldAlert className="w-5 h-5 text-white" />
          </div>
          <span className="font-bold text-[18px] tracking-tight group-hover:text-indigo-100 transition-colors">
            GovConnect
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto py-8 px-4 space-y-2 scrollbar-hide">
        <div className="text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-4 px-3">
          Overview
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.name}
              to={item.path}
              end={item.end}
              className={({ isActive }) =>
                `group relative flex items-center gap-3 px-3 py-3 rounded-xl font-medium transition-colors duration-300 ${
                  isActive ? 'text-white' : 'text-slate-400 hover:text-slate-200'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <motion.div
                      layoutId="sidebar-highlight"
                      className="absolute inset-0 bg-indigo-500/20 rounded-xl border border-indigo-500/20"
                      initial={false}
                      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                    />
                  )}
                  <Icon className={`w-5 h-5 relative z-10 transition-colors duration-300 ${isActive ? 'text-indigo-400' : 'text-slate-500 group-hover:text-slate-300'}`} />
                  <span className="relative z-10">{item.name}</span>
                </>
              )}
            </NavLink>
          );
        })}
      </div>

      <div className="p-4 border-t border-white/5 space-y-2 mb-2">
        <button className="group relative flex items-center gap-3 px-3 py-3 w-full text-left rounded-xl font-medium text-slate-400 hover:text-slate-200 transition-colors duration-300">
          <div className="absolute inset-0 bg-slate-800/0 group-hover:bg-slate-800/50 rounded-xl transition-colors duration-300" />
          <Settings className="w-5 h-5 relative z-10 text-slate-500 group-hover:text-slate-300 transition-colors" />
          <span className="relative z-10">Settings</span>
        </button>
        <button className="group relative flex items-center gap-3 px-3 py-3 w-full text-left rounded-xl font-medium text-slate-400 hover:text-rose-400 transition-colors duration-300">
          <div className="absolute inset-0 bg-rose-500/0 group-hover:bg-rose-500/10 rounded-xl transition-colors duration-300" />
          <LogOut className="w-5 h-5 relative z-10 text-slate-500 group-hover:text-rose-400 transition-colors" />
          <span className="relative z-10">Logout</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
