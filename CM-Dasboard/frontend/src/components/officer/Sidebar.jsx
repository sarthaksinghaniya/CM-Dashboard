import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { LayoutDashboard, FileText, BarChart3, Settings, LogOut, ShieldAlert } from 'lucide-react';

const Sidebar = () => {
  const location = useLocation();
  const isAdmin = location.pathname.startsWith('/admin');
  
  const navItems = isAdmin 
    ? [
        { name: 'Dashboard', path: '/admin', icon: LayoutDashboard, end: true },
        { name: 'Complaints', path: '/admin/complaints', icon: FileText, end: false },
        { name: 'Analytics', path: '/admin/analytics', icon: BarChart3, end: false },
      ]
    : [
        { name: 'Dashboard', path: '/officer/dashboard', icon: LayoutDashboard, end: true },
        { name: 'Complaints', path: '/officer', icon: FileText, end: true },
        { name: 'Analytics', path: '/officer/analytics', icon: BarChart3, end: false },
      ];

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 text-slate-300 flex flex-col h-full shrink-0 transition-all duration-300 shadow-xl">
      <div className="h-16 flex items-center px-6 border-b border-white/5">
        <div className="flex items-center gap-3 text-white w-full group cursor-pointer">
          <div className="w-9 h-9 bg-gradient-to-br from-indigo-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/20 group-hover:shadow-indigo-500/40 transition-shadow">
            <ShieldAlert className="w-5 h-5 text-white" />
          </div>
          <span className="font-bold text-[17px] tracking-tight group-hover:text-indigo-100 transition-colors">
            {isAdmin ? 'Admin Portal' : 'Officer Portal'}
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto py-8 px-4 space-y-1 scrollbar-hide">
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
                `group flex items-center gap-3 px-3 py-2.5 rounded-xl font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-indigo-500/10 text-indigo-400'
                    : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon className={`w-5 h-5 transition-colors duration-200 ${isActive ? 'text-indigo-400' : 'text-slate-500 group-hover:text-slate-300'}`} />
                  {item.name}
                </>
              )}
            </NavLink>
          );
        })}
      </div>

      <div className="p-4 border-t border-white/5 space-y-1 mb-2">
        <button className="group flex items-center gap-3 px-3 py-2.5 w-full text-left rounded-xl font-medium text-slate-400 hover:bg-slate-800/50 hover:text-slate-200 transition-all duration-200">
          <Settings className="w-5 h-5 text-slate-500 group-hover:text-slate-300 transition-colors" />
          Settings
        </button>
        <button className="group flex items-center gap-3 px-3 py-2.5 w-full text-left rounded-xl font-medium text-slate-400 hover:bg-rose-500/10 hover:text-rose-400 transition-all duration-200">
          <LogOut className="w-5 h-5 text-slate-500 group-hover:text-rose-400 transition-colors" />
          Logout
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
