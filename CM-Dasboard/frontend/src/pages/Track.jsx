import React, { useState } from 'react';
import { trackComplaint } from '../services/api';
import Loader from '../components/Loader';
import StatusBadge from '../components/StatusBadge';
import { Search, MapPin, User, Clock, CheckCircle } from 'lucide-react';

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

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-fade-in">
      <div className="text-center space-y-4 py-6">
        <h1 className="text-3xl font-bold text-slate-800">Track Complaint Status</h1>
        <p className="text-slate-500">Enter your Ticket ID below to check real-time updates.</p>
      </div>

      <div className="glass-panel p-2 flex items-center shadow-md">
        <form onSubmit={handleSearch} className="flex-1 flex items-center">
          <div className="px-4 text-slate-400">
            <Search className="w-5 h-5" />
          </div>
          <input
            type="text"
            value={ticketId}
            onChange={(e) => setTicketId(e.target.value)}
            placeholder="e.g., TKT-12345"
            className="flex-1 py-3 bg-transparent outline-none text-slate-700 font-medium placeholder:font-normal"
          />
          <button type="submit" disabled={loading} className="btn-primary ml-2 py-3 px-6">
            Track
          </button>
        </form>
      </div>

      {loading && <Loader />}

      {error && (
        <div className="bg-rose-50 text-rose-600 p-4 rounded-xl text-center font-medium border border-rose-100 animate-slide-up">
          {error}
        </div>
      )}

      {complaint && (
        <div className="glass-panel p-8 animate-slide-up space-y-8">
          <div className="flex flex-col md:flex-row justify-between md:items-center gap-4 pb-6 border-b border-slate-100">
            <div>
              <p className="text-sm text-slate-500 font-medium mb-1">Ticket #{complaint.id || ticketId}</p>
              <h2 className="text-2xl font-bold text-slate-800">{complaint.title || 'Untitled Complaint'}</h2>
            </div>
            <StatusBadge status={complaint.status} className="text-sm px-3 py-1" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Details</h3>
              <p className="text-slate-700 leading-relaxed">{complaint.description}</p>
            </div>
            
            <div className="bg-slate-50 rounded-xl p-5 space-y-4 border border-slate-100">
              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Meta Info</h3>
              
              <div className="flex items-center gap-3 text-slate-600">
                <MapPin className="w-4 h-4 text-primary-500" />
                <span className="font-medium">{complaint.location || complaint.district || 'Location N/A'}</span>
              </div>
              
              <div className="flex items-center gap-3 text-slate-600">
                <User className="w-4 h-4 text-primary-500" />
                <span className="font-medium">Assigned: {complaint.assigned_officer || 'Pending Assignment'}</span>
              </div>
              
              <div className="flex items-center gap-3 text-slate-600">
                <Clock className="w-4 h-4 text-primary-500" />
                <span className="font-medium">Priority: <span className="capitalize">{complaint.priority || 'Normal'}</span></span>
              </div>
            </div>
          </div>
          
          {/* Mock Timeline - can be connected to real data if backend supports it */}
          <div className="pt-6 border-t border-slate-100">
             <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">Progress</h3>
             <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-emerald-500" />
                <span className="text-sm font-medium text-emerald-700">Complaint Submitted</span>
                <div className="flex-1 h-px bg-slate-200 mx-2"></div>
                <div className={`w-3 h-3 rounded-full ${complaint.status?.toLowerCase() !== 'pending' ? 'bg-emerald-500' : 'bg-slate-300'}`}></div>
                <span className={`text-sm font-medium ${complaint.status?.toLowerCase() !== 'pending' ? 'text-emerald-700' : 'text-slate-400'}`}>In Progress</span>
                <div className="flex-1 h-px bg-slate-200 mx-2"></div>
                <div className={`w-3 h-3 rounded-full ${complaint.status?.toLowerCase() === 'resolved' ? 'bg-emerald-500' : 'bg-slate-300'}`}></div>
                <span className={`text-sm font-medium ${complaint.status?.toLowerCase() === 'resolved' ? 'text-emerald-700' : 'text-slate-400'}`}>Resolved</span>
             </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Track;
