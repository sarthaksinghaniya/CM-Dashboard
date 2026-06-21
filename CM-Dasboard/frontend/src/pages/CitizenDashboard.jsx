import React from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';
import AnimatedPage from '../components/AnimatedPage';
import { FileText, AlertCircle, Clock, CheckCircle } from 'lucide-react';
import { motion } from 'framer-motion';

export default function CitizenDashboard() {
  const { data: complaints = [], isLoading, isError } = useQuery({
    queryKey: ['myComplaints'],
    queryFn: async () => {
      const res = await api.get('/complaints/my-complaints');
      return res.data;
    }
  });

  const getStatusColor = (status) => {
    switch(status?.toLowerCase()) {
      case 'resolved': return 'bg-emerald-100 text-emerald-700 border-emerald-200';
      case 'in_progress': return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'rejected': return 'bg-rose-100 text-rose-700 border-rose-200';
      default: return 'bg-amber-100 text-amber-700 border-amber-200';
    }
  };

  return (
    <AnimatedPage className="space-y-6">
      <div>
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">My Complaints</h1>
        <p className="text-slate-500 mt-1">View and track the status of your submitted complaints.</p>
      </div>

      {isLoading ? (
        <div className="flex justify-center p-12">
          <div className="w-8 h-8 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin" />
        </div>
      ) : isError ? (
        <div className="bg-rose-50 text-rose-600 p-4 rounded-xl flex items-center gap-3">
          <AlertCircle className="w-5 h-5" />
          <span>Failed to load your complaints.</span>
        </div>
      ) : complaints.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center shadow-sm">
          <div className="w-16 h-16 bg-slate-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <FileText className="w-8 h-8 text-slate-400" />
          </div>
          <h3 className="text-lg font-bold text-slate-900 mb-1">No Complaints Found</h3>
          <p className="text-slate-500">You haven't submitted any complaints yet.</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {complaints.map((c, i) => (
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              key={c.ticket_id} 
              className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-3 mb-1">
                    <span className="font-mono text-sm font-bold text-slate-500">{c.ticket_id}</span>
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${getStatusColor(c.status)}`}>
                      {c.status}
                    </span>
                  </div>
                  <h3 className="font-bold text-slate-800 text-lg">Category: {c.category}</h3>
                  <div className="text-sm text-slate-500 flex items-center gap-4 mt-2">
                    <span className="flex items-center gap-1.5"><AlertCircle className="w-4 h-4"/> Priority: {c.priority}</span>
                    <span className="flex items-center gap-1.5"><Clock className="w-4 h-4"/> {new Date(c.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </AnimatedPage>
  );
}
