import React from 'react';

const StatsCard = ({ title, count, icon: Icon, colorClass }) => {
  return (
    <div className="group bg-white rounded-2xl shadow-[0_2px_10px_rgb(0,0,0,0.04)] border border-slate-200/60 p-6 flex items-center justify-between hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)] hover:-translate-y-1 transition-all duration-300 ease-out cursor-default relative overflow-hidden">
      {/* Subtle background glow effect on hover */}
      <div className={`absolute -inset-4 opacity-0 group-hover:opacity-10 transition-opacity duration-500 blur-2xl rounded-full ${colorClass.split(' ')[0]}`} />
      
      <div className="relative z-10">
        <p className="text-sm font-semibold text-slate-500 uppercase tracking-wider">{title}</p>
        <h3 className="text-4xl font-extrabold text-slate-800 mt-2 tracking-tight">{count}</h3>
      </div>
      
      <div className={`relative z-10 w-14 h-14 rounded-2xl flex items-center justify-center shadow-inner border border-white/50 ${colorClass}`}>
        <Icon className="w-7 h-7" />
      </div>
    </div>
  );
};

export default StatsCard;
