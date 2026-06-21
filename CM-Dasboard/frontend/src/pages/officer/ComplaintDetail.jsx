import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { trackComplaint, updateComplaintStatus } from '../../services/api'; // using trackComplaint to get by ID
import StatusBadge from '../../components/StatusBadge';
import Loader from '../../components/Loader';
import { ArrowLeft, MapPin, Clock, User, CheckCircle, AlertTriangle, Paperclip, Save } from 'lucide-react';

const ComplaintDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [complaint, setComplaint] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Update state
  const [newStatus, setNewStatus] = useState('');
  const [remarks, setRemarks] = useState('');
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    fetchComplaintDetail();
  }, [id]);

  const fetchComplaintDetail = async () => {
    try {
      setLoading(true);
      const data = await trackComplaint(id);
      setComplaint(data);
      setNewStatus(data.status || 'pending');
    } catch (err) {
      setError('Failed to fetch complaint details.');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = async () => {
    try {
      setUpdating(true);
      await updateComplaintStatus(id, newStatus);
      // Optimistic UI update or re-fetch
      setComplaint({ ...complaint, status: newStatus });
      alert('Status updated successfully!');
    } catch (err) {
      alert('Failed to update status.');
    } finally {
      setUpdating(false);
    }
  };

  if (loading) return <div className="py-20"><Loader /></div>;
  
  if (error || !complaint) return (
    <div className="bg-rose-50 text-rose-600 p-6 rounded-xl border border-rose-100 text-center animate-fade-in">
      <AlertTriangle className="w-8 h-8 mx-auto mb-2" />
      <h3 className="text-lg font-bold">Error</h3>
      <p>{error || 'Complaint not found.'}</p>
      <button onClick={() => navigate('/officer')} className="mt-4 px-4 py-2 bg-white text-rose-600 rounded-lg border border-rose-200">
        Back to List
      </button>
    </div>
  );

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between bg-white p-4 rounded-xl shadow-sm border border-slate-200">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => navigate('/officer')}
            className="p-2 hover:bg-slate-100 rounded-lg text-slate-500 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-xl font-bold text-slate-800">Ticket #{complaint.id || id}</h1>
            <p className="text-sm text-slate-500">{complaint.title || 'Untitled Complaint'}</p>
          </div>
        </div>
        <StatusBadge status={complaint.status} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Details */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-6">
            <h2 className="text-lg font-bold text-slate-800 border-b border-slate-100 pb-2">Complaint Details</h2>
            
            <p className="text-slate-700 leading-relaxed whitespace-pre-wrap">
              {complaint.description}
            </p>

            <div className="grid grid-cols-2 gap-4 pt-4">
              <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                <div className="text-xs font-semibold text-slate-400 uppercase mb-1 flex items-center gap-1"><MapPin className="w-3 h-3"/> Location</div>
                <div className="font-medium text-slate-800">{complaint.district || complaint.location || 'N/A'}</div>
              </div>
              <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                <div className="text-xs font-semibold text-slate-400 uppercase mb-1 flex items-center gap-1"><User className="w-3 h-3"/> Complainant</div>
                <div className="font-medium text-slate-800">User #{complaint.complainant_id || 'Anonymous'}</div>
              </div>
              <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                <div className="text-xs font-semibold text-slate-400 uppercase mb-1 flex items-center gap-1"><Clock className="w-3 h-3"/> Submitted On</div>
                <div className="font-medium text-slate-800">{complaint.created_at ? new Date(complaint.created_at).toLocaleString() : 'N/A'}</div>
              </div>
              <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                <div className="text-xs font-semibold text-slate-400 uppercase mb-1 flex items-center gap-1"><AlertTriangle className="w-3 h-3"/> Priority</div>
                <div className="font-medium text-slate-800 capitalize">{complaint.priority || 'Normal'}</div>
              </div>
            </div>
            
            {/* Attachments Mock */}
            <div className="pt-4 border-t border-slate-100">
              <h3 className="text-sm font-semibold text-slate-800 mb-3">Attachments</h3>
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-600 hover:bg-slate-100 cursor-pointer transition-colors">
                  <Paperclip className="w-4 h-4 text-slate-400" />
                  <span>evidence_photo.jpg</span>
                </div>
              </div>
            </div>
          </div>

          {/* Timeline reuse */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h2 className="text-lg font-bold text-slate-800 mb-6">Progress Timeline</h2>
            <div className="flex items-center gap-2 w-full max-w-lg mx-auto">
                <CheckCircle className="w-6 h-6 text-emerald-500" />
                <div className={`flex-1 h-1 ${complaint.status?.toLowerCase() !== 'pending' ? 'bg-emerald-500' : 'bg-slate-200'}`}></div>
                <div className={`w-4 h-4 rounded-full ${complaint.status?.toLowerCase() !== 'pending' ? 'bg-emerald-500' : 'bg-slate-300'}`}></div>
                <div className={`flex-1 h-1 ${complaint.status?.toLowerCase() === 'resolved' ? 'bg-emerald-500' : 'bg-slate-200'}`}></div>
                <div className={`w-4 h-4 rounded-full ${complaint.status?.toLowerCase() === 'resolved' ? 'bg-emerald-500' : 'bg-slate-300'}`}></div>
            </div>
            <div className="flex justify-between w-full max-w-lg mx-auto mt-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
              <span>Submitted</span>
              <span>In Progress</span>
              <span>Resolved</span>
            </div>
          </div>
        </div>

        {/* Right Column - Actions */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-5 sticky top-24">
            <h2 className="text-lg font-bold text-slate-800 border-b border-slate-100 pb-2">Update Resolution</h2>
            
            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-700 block">Change Status</label>
              <select 
                value={newStatus}
                onChange={(e) => setNewStatus(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none p-2.5 text-slate-700"
              >
                <option value="pending">Pending</option>
                <option value="in progress">In Progress</option>
                <option value="resolved">Resolved</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-700 block">Officer Remarks</label>
              <textarea 
                rows="4"
                value={remarks}
                onChange={(e) => setRemarks(e.target.value)}
                placeholder="Add internal notes or resolution remarks..."
                className="w-full bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none p-3 text-slate-700 resize-none text-sm"
              ></textarea>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-700 block">Upload Proof</label>
              <div className="border-2 border-dashed border-slate-200 rounded-lg p-4 text-center hover:bg-slate-50 transition-colors cursor-pointer">
                <Paperclip className="w-5 h-5 text-slate-400 mx-auto mb-1" />
                <span className="text-xs text-slate-500">Click to upload files</span>
              </div>
            </div>

            <button 
              onClick={handleUpdate}
              disabled={updating || newStatus === complaint.status}
              className={`w-full flex items-center justify-center gap-2 py-3 rounded-lg font-bold transition-all ${
                updating || newStatus === complaint.status 
                  ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                  : 'bg-primary-600 text-white hover:bg-primary-700 shadow-md hover:shadow-lg active:scale-95'
              }`}
            >
              <Save className="w-5 h-5" />
              {updating ? 'Saving...' : 'Save Update'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ComplaintDetail;
