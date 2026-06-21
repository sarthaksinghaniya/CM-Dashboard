import React from 'react';
import { motion } from 'framer-motion';

const StatsCard = ({ title, count, icon: Icon, colorClass }) => {
  return (
    <motion.div 
      whileHover={{ scale: 1.02, y: -4 }}
      whileTap={{ scale: 0.98 }}
      className="bg-white/80 backdrop-blur-xl rounded-2xl p-6 shadow-sm border border-slate-200/60 hover:shadow-xl hover:shadow-slate-200/50 transition-shadow duration-300 relative overflow-hidden group cursor-pointer"
    >
      <div className="absolute top-2 right-2 p-2 opacity-5 group-hover:opacity-10 transition-opacity duration-300">
        <Icon className="w-16 h-16" />
      </div>
      <div className="flex items-center gap-4 relative z-10">
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${colorClass} group-hover:scale-110 transition-transform duration-300`}>
          <Icon className="w-6 h-6" />
        </div>
        <div>
          <p className="text-sm font-bold text-slate-400 uppercase tracking-widest">{title}</p>
          <h3 className="text-3xl font-black text-slate-800 mt-1 tracking-tight">{count}</h3>
        </div>
      </div>
    </motion.div>
  );
};

export default StatsCard;
