import React, { useState } from 'react';
import { trackComplaint } from '../services/api';
import Loader from '../components/Loader';
import StatusBadge from '../components/StatusBadge';
import AnimatedPage from '../components/AnimatedPage';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, MapPin, User, Clock, CheckCircle2, Circle, AlertCircle } from 'lucide-react';

const Track = () => {
  const [ticketId, setTicketId] = useState('');
  const [complaint, setComplaint] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!ticketId.trim()) return;

    setLoading(true);
    setError('');
    setComplaint(null);

    try {
      const res = await trackComplaint(ticketId);
      setComplaint(res);
    } catch (err) {
      setError('Complaint not found or invalid Ticket ID.');
    } finally {
      setLoading(false);
    }
  };

  const getTimelineStatus = (status) => {
    const s = status?.toLowerCase() || '';
    if (s === 'resolved' || s === 'completed') return 3;
    if (s === 'in progress' || s === 'in_progress') return 2;
    return 1; // pending
  };

  const step = complaint ? getTimelineStatus(complaint.status) : 0;

  return (
    <AnimatedPage className="relative min-h-[85vh] flex flex-col items-center py-12 px-4 sm:px-6 lg:px-8">
      {/* Background ambient gradients */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none -z-10">
        <motion.div 
          animate={{ scale: [1, 1.2, 1], opacity: [0.5, 0.8, 0.5] }}
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
          className="absolute top-[10%] -left-[10%] w-[40%] h-[40%] rounded-full bg-blue-400/20 blur-[120px]" 
        />
        <motion.div 
          animate={{ scale: [1, 1.3, 1], opacity: [0.4, 0.7, 0.4] }}
          transition={{ duration: 10, repeat: Infinity, ease: "easeInOut", delay: 2 }}
          className="absolute top-[50%] -right-[10%] w-[30%] h-[50%] rounded-full bg-emerald-400/20 blur-[120px]" 
        />
      </div>

      <div className="w-full max-w-3xl mx-auto space-y-8">
        
        {/* Header Section */}
        <div className="text-center space-y-4">
          <motion.div 
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", stiffness: 200, damping: 20 }}
            className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-tr from-slate-100 to-white text-slate-600 mb-2 shadow-sm border border-white/50 backdrop-blur-sm"
          >
            <Search className="w-8 h-8" />
          </motion.div>
          <h1 className="text-4xl md:text-5xl font-extrabold text-slate-800 tracking-tight">
            Track <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">Status</span>
          </h1>
          <p className="text-lg text-slate-500 font-medium">
            Enter your Ticket ID below to check real-time updates.
          </p>
        </div>

        {/* Search Bar Card */}
        <motion.div 
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="relative bg-white/70 backdrop-blur-xl border border-white shadow-md rounded-2xl p-4 overflow-hidden focus-within:ring-2 focus-within:ring-blue-500/20 transition-shadow"
        >
          <form onSubmit={handleSearch} className="flex items-center">
            <div className="pl-4 pr-3 text-slate-400">
              <Search className="w-6 h-6" />
            </div>
            <input
              type="text"
              value={ticketId}
              onChange={(e) => setTicketId(e.target.value)}
              placeholder="e.g., TKT-12345"
              className="flex-1 py-3 bg-transparent outline-none text-slate-800 font-bold text-lg placeholder:font-medium placeholder:text-slate-400"
            />
            <button 
              type="submit" 
              disabled={loading} 
              className={`ml-2 py-3 px-8 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold rounded-xl shadow-md transition-all duration-300 flex items-center justify-center min-w-[120px] ${loading ? 'opacity-70 cursor-not-allowed' : 'hover:shadow-lg hover:shadow-blue-500/30 hover:-translate-y-0.5 active:scale-95'}`}
            >
              {loading ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : 'Track'}
            </button>
          </form>
        </motion.div>

        <AnimatePresence>
          {error && (
            <motion.div 
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="bg-rose-50/90 backdrop-blur-sm text-rose-600 p-4 rounded-xl text-center font-medium border border-rose-100 flex items-center justify-center gap-2 shadow-sm"
            >
              <AlertCircle className="w-5 h-5" />
              {error}
            </motion.div>
          )}

          {/* Results Card */}
          {complaint && (
            <motion.div 
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ type: "spring", stiffness: 200, damping: 25 }}
              className="bg-white/80 backdrop-blur-xl border border-white/80 shadow-[0_8px_30px_rgb(0,0,0,0.06)] rounded-3xl p-8 space-y-8"
            >
              {/* Header */}
              <div className="flex flex-col md:flex-row justify-between md:items-start gap-4 pb-6 border-b border-slate-200/60">
                <div>
                  <p className="text-sm text-slate-500 font-bold tracking-widest uppercase mb-2">Ticket #{complaint.id || ticketId}</p>
                  <h2 className="text-2xl font-extrabold text-slate-900 leading-tight">{complaint.title || 'Untitled Complaint'}</h2>
                </div>
                <StatusBadge status={complaint.status} className="text-sm px-4 py-1.5 shadow-sm" />
              </div>

              {/* Details Grid */}
              <div className="grid grid-cols-1 md:grid-cols-5 gap-8">
                <div className="md:col-span-3 space-y-3">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">Description</h3>
                  <p className="text-slate-700 font-medium leading-relaxed bg-slate-50/50 p-4 rounded-xl border border-slate-100">{complaint.description}</p>
                </div>
                
                <div className="md:col-span-2 bg-gradient-to-br from-slate-50 to-white rounded-2xl p-6 space-y-5 border border-slate-200/60 shadow-inner">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">Meta Info</h3>
                  
                  <div className="flex items-center gap-3.5 text-slate-700">
                    <div className="p-2 bg-blue-100 text-blue-600 rounded-lg"><MapPin className="w-4 h-4" /></div>
                    <span className="font-semibold">{complaint.location || complaint.district || 'Location N/A'}</span>
                  </div>
                  
                  <div className="flex items-center gap-3.5 text-slate-700">
                    <div className="p-2 bg-indigo-100 text-indigo-600 rounded-lg"><User className="w-4 h-4" /></div>
                    <span className="font-semibold">{complaint.assigned_officer || 'Pending Assignment'}</span>
                  </div>
                  
                  <div className="flex items-center gap-3.5 text-slate-700">
                    <div className="p-2 bg-amber-100 text-amber-600 rounded-lg"><Clock className="w-4 h-4" /></div>
                    <span className="font-semibold">Priority: <span className="capitalize">{complaint.priority || 'Normal'}</span></span>
                  </div>
                </div>
              </div>
              
              {/* Timeline Progress */}
              <div className="pt-6 border-t border-slate-200/60">
                 <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-6">Progress</h3>
                 <div className="flex items-center justify-between relative">
                    {/* Background Line */}
                    <div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-1 bg-slate-100 rounded-full"></div>
                    {/* Active Line */}
                    <motion.div 
                      initial={{ width: '0%' }}
                      animate={{ width: step === 1 ? '0%' : step === 2 ? '50%' : '100%' }}
                      transition={{ duration: 1, delay: 0.3, ease: "easeOut" }}
                      className="absolute left-0 top-1/2 -translate-y-1/2 h-1 bg-blue-500 rounded-full"
                    ></motion.div>

                    {/* Step 1 */}
                    <div className="relative flex flex-col items-center gap-2 bg-white px-2">
                      <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.5, type: 'spring' }}>
                        {step >= 1 ? <CheckCircle2 className="w-8 h-8 text-blue-500 bg-white rounded-full" /> : <Circle className="w-8 h-8 text-slate-300 bg-white rounded-full" />}
                      </motion.div>
                      <span className={`text-xs font-bold ${step >= 1 ? 'text-blue-700' : 'text-slate-400'}`}>Submitted</span>
                    </div>

                    {/* Step 2 */}
                    <div className="relative flex flex-col items-center gap-2 bg-white px-2">
                      <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.9, type: 'spring' }}>
                        {step >= 2 ? <CheckCircle2 className="w-8 h-8 text-blue-500 bg-white rounded-full" /> : <Circle className="w-8 h-8 text-slate-300 bg-white rounded-full" />}
                      </motion.div>
                      <span className={`text-xs font-bold ${step >= 2 ? 'text-blue-700' : 'text-slate-400'}`}>In Progress</span>
                    </div>

                    {/* Step 3 */}
                    <div className="relative flex flex-col items-center gap-2 bg-white px-2">
                      <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 1.3, type: 'spring' }}>
                        {step >= 3 ? <CheckCircle2 className="w-8 h-8 text-emerald-500 bg-white rounded-full" /> : <Circle className="w-8 h-8 text-slate-300 bg-white rounded-full" />}
                      </motion.div>
                      <span className={`text-xs font-bold ${step >= 3 ? 'text-emerald-700' : 'text-slate-400'}`}>Resolved</span>
                    </div>
                 </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </AnimatedPage>
  );
};

export default Track;
