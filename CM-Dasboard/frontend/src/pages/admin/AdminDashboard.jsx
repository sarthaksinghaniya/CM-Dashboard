import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { useOfficerComplaints } from '../../services/queries';
import StatsCard from '../../components/admin/StatsCard';
import Charts from '../../components/admin/Charts';
import ComplaintTable from '../../components/officer/ComplaintTable';
import Loader from '../../components/Loader';
import AnimatedPage from '../../components/AnimatedPage';
import { LayoutDashboard, CheckCircle2, Clock, AlertCircle } from 'lucide-react';

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 300, damping: 24 } }
};

const AdminDashboard = () => {
  const { data, isLoading, isError, error, refetch } = useOfficerComplaints();
  
  const complaints = useMemo(() => {
    if (!data) return [];
    return Array.isArray(data) ? data : data.items || [];
  }, [data]);

  const stats = useMemo(() => {
    let pending = 0;
    let inProgress = 0;
    let resolved = 0;

    complaints.forEach(c => {
      const status = (c.status || 'pending').toLowerCase();
      if (status === 'pending') pending++;
      else if (status === 'in progress') inProgress++;
      else if (status === 'resolved') resolved++;
    });

    return {
      total: complaints.length,
      pending,
      inProgress,
      resolved
    };
  }, [complaints]);

  if (isLoading) {
    return <div className="py-20 flex items-center justify-center"><Loader /></div>;
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
        <div className="p-4 bg-rose-100 text-rose-600 rounded-full">
          <AlertCircle className="w-12 h-12" />
        </div>
        <h2 className="text-2xl font-bold text-slate-800">Failed to load data</h2>
        <p className="text-slate-500 max-w-md text-center">{error?.message || 'A network error occurred.'}</p>
        <button 
          onClick={() => refetch()}
          className="px-6 py-2 bg-slate-900 text-white rounded-xl shadow-md font-medium hover:bg-slate-800 transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <AnimatedPage className="space-y-8 max-w-7xl mx-auto">
      <div>
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Dashboard Overview</h1>
        <p className="text-sm font-medium text-slate-500 mt-1">High-level view of system performance and active complaints.</p>
      </div>

      {/* Stats Cards Row */}
      <motion.div 
        variants={containerVariants} 
        initial="hidden" 
        animate="show" 
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6"
      >
        <motion.div variants={itemVariants}>
          <StatsCard 
            title="Total Complaints" 
            count={stats.total} 
            icon={LayoutDashboard} 
            colorClass="bg-indigo-100 text-indigo-600" 
          />
        </motion.div>
        <motion.div variants={itemVariants}>
          <StatsCard 
            title="Pending" 
            count={stats.pending} 
            icon={AlertCircle} 
            colorClass="bg-amber-100 text-amber-600" 
          />
        </motion.div>
        <motion.div variants={itemVariants}>
          <StatsCard 
            title="In Progress" 
            count={stats.inProgress} 
            icon={Clock} 
            colorClass="bg-blue-100 text-blue-600" 
          />
        </motion.div>
        <motion.div variants={itemVariants}>
          <StatsCard 
            title="Resolved" 
            count={stats.resolved} 
            icon={CheckCircle2} 
            colorClass="bg-emerald-100 text-emerald-600" 
          />
        </motion.div>
      </motion.div>

      {/* Charts Section */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }} 
        animate={{ opacity: 1, y: 0 }} 
        transition={{ delay: 0.4, type: 'spring', stiffness: 200, damping: 20 }}
      >
        <Charts complaints={complaints} />
      </motion.div>

      {/* Recent Complaints Table */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }} 
        animate={{ opacity: 1, y: 0 }} 
        transition={{ delay: 0.5, type: 'spring', stiffness: 200, damping: 20 }}
        className="space-y-4"
      >
        <div className="flex items-center justify-between px-1">
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Recent Complaints</h2>
          <a href="/complaints" className="text-sm font-bold text-blue-600 hover:text-blue-700 hover:underline transition-colors">
            View All
          </a>
        </div>
        <ComplaintTable complaints={complaints.slice(0, 5)} />
      </motion.div>
    </AnimatedPage>
  );
};

export default AdminDashboard;
