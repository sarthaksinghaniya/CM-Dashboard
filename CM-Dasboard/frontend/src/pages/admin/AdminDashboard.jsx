import React, { useState, useEffect, useMemo } from 'react';
import { getOfficerComplaints } from '../../services/api';
import StatsCard from '../../components/admin/StatsCard';
import Charts from '../../components/admin/Charts';
import ComplaintTable from '../../components/officer/ComplaintTable';
import Loader from '../../components/Loader';
import { LayoutDashboard, CheckCircle2, Clock, AlertCircle } from 'lucide-react';

const AdminDashboard = () => {
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const data = await getOfficerComplaints();
      setComplaints(Array.isArray(data) ? data : data.items || []);
    } catch (error) {
      console.error('Failed to fetch dashboard data', error);
    } finally {
      setLoading(false);
    }
  };

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

  if (loading) {
    return <div className="py-20 flex items-center justify-center"><Loader /></div>;
  }

  return (
    <div className="space-y-8 animate-fade-in max-w-7xl mx-auto">
      <div>
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Admin Overview</h1>
        <p className="text-sm font-medium text-slate-500 mt-1">High-level view of system performance and active complaints.</p>
      </div>

      {/* Stats Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard 
          title="Total Complaints" 
          count={stats.total} 
          icon={LayoutDashboard} 
          colorClass="bg-indigo-100 text-indigo-600" 
        />
        <StatsCard 
          title="Pending" 
          count={stats.pending} 
          icon={AlertCircle} 
          colorClass="bg-amber-100 text-amber-600" 
        />
        <StatsCard 
          title="In Progress" 
          count={stats.inProgress} 
          icon={Clock} 
          colorClass="bg-blue-100 text-blue-600" 
        />
        <StatsCard 
          title="Resolved" 
          count={stats.resolved} 
          icon={CheckCircle2} 
          colorClass="bg-emerald-100 text-emerald-600" 
        />
      </div>

      {/* Charts Section */}
      <div>
        <Charts complaints={complaints} />
      </div>

      {/* Recent Complaints Table */}
      <div className="space-y-4">
        <div className="flex items-center justify-between px-1">
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Recent Complaints</h2>
          <a href="/admin/complaints" className="text-sm font-bold text-indigo-600 hover:text-indigo-700 hover:underline transition-colors">
            View All
          </a>
        </div>
        <ComplaintTable complaints={complaints.slice(0, 5)} />
      </div>
    </div>
  );
};

export default AdminDashboard;
