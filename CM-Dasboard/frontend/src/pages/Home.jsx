import React, { useState } from 'react';
import { submitComplaint } from '../services/api';
import Loader from '../components/Loader';
import { CheckCircle2, ShieldAlert, FileText, MapPin, AlignLeft, ArrowRight } from 'lucide-react';

const Home = () => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    district: '',
  });
  const [loading, setLoading] = useState(false);
  const [successTicket, setSuccessTicket] = useState(null);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccessTicket(null);

    try {
      const res = await submitComplaint({
        title: formData.title,
        description: formData.description,
        location: formData.district,
        complainant_id: 1,
      });
      setSuccessTicket(res.id || res.ticket_id || 'TICKET-GEN');
      setFormData({ title: '', description: '', district: '' });
    } catch (err) {
      setError('Failed to submit complaint. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-[85vh] flex flex-col items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      {/* Background ambient gradients */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none -z-10">
        <div className="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] rounded-full bg-blue-400/20 blur-[120px]" />
        <div className="absolute top-[40%] -right-[10%] w-[40%] h-[60%] rounded-full bg-indigo-400/10 blur-[120px]" />
      </div>

      <div className="w-full max-w-2xl mx-auto space-y-8 animate-fade-in">
        
        {/* Header Section */}
        <div className="text-center space-y-4">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-tr from-blue-100 to-indigo-50 text-blue-600 mb-2 shadow-sm border border-white/50 backdrop-blur-sm">
            <ShieldAlert className="w-8 h-8" />
          </div>
          <h1 className="text-4xl md:text-5xl font-extrabold text-slate-800 tracking-tight">
            File a <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">Complaint</span>
          </h1>
          <p className="text-lg text-slate-500 max-w-xl mx-auto font-medium">
            Submit your grievances securely. Our system ensures your voice is heard and issues are resolved efficiently.
          </p>
        </div>

        {/* Form Card (Glassmorphism) */}
        <div className="relative bg-white/60 backdrop-blur-xl border border-white/80 shadow-[0_8px_30px_rgb(0,0,0,0.04)] rounded-2xl p-8 md:p-10 overflow-hidden">
          {loading && (
            <div className="absolute inset-0 bg-white/50 backdrop-blur-sm z-10 flex items-center justify-center">
              <Loader fullScreen={false} />
            </div>
          )}

          {successTicket ? (
            <div className="text-center space-y-6 py-10 animate-slide-up">
              <div className="mx-auto w-20 h-20 bg-gradient-to-tr from-emerald-100 to-teal-50 rounded-full flex items-center justify-center text-emerald-600 shadow-sm border border-white/50">
                <CheckCircle2 className="w-10 h-10" />
              </div>
              <div>
                <h2 className="text-3xl font-bold text-slate-800 tracking-tight">Success!</h2>
                <p className="text-slate-500 mt-2 font-medium">Your complaint has been securely filed.</p>
                
                <div className="mt-8 p-6 bg-gradient-to-br from-slate-50 to-slate-100/50 rounded-2xl border border-slate-200/60 shadow-inner">
                  <p className="text-sm font-semibold text-slate-400 uppercase tracking-widest mb-2">Ticket ID</p>
                  <div className="font-mono text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600 tracking-wider">
                    {successTicket}
                  </div>
                </div>
              </div>
              <p className="text-sm text-slate-500 mt-4">
                Please save this ID. You can use it to track the status of your complaint at any time.
              </p>
              <button
                onClick={() => setSuccessTicket(null)}
                className="mt-8 w-full py-3.5 px-4 bg-white text-slate-700 font-semibold rounded-xl border border-slate-200 shadow-sm hover:bg-slate-50 hover:shadow transition-all duration-200 active:scale-[0.98]"
              >
                Submit Another Complaint
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-6">
              {error && (
                <div className="bg-rose-50/80 backdrop-blur-sm text-rose-600 p-4 rounded-xl text-sm font-medium border border-rose-100 flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4" />
                  {error}
                </div>
              )}

              <div className="space-y-1.5 group">
                <label className="text-sm font-semibold text-slate-700 flex items-center gap-2 ml-1">
                  <FileText className="w-4 h-4 text-slate-400 group-focus-within:text-blue-500 transition-colors" />
                  Complaint Title
                </label>
                <input
                  type="text"
                  name="title"
                  required
                  value={formData.title}
                  onChange={handleChange}
                  placeholder="Brief summary of the issue"
                  className="w-full px-4 py-3.5 bg-white/80 border border-slate-200 rounded-xl focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 outline-none transition-all duration-300 shadow-sm hover:bg-white placeholder:text-slate-400 text-slate-800 font-medium"
                />
              </div>

              <div className="space-y-1.5 group">
                <label className="text-sm font-semibold text-slate-700 flex items-center gap-2 ml-1">
                  <AlignLeft className="w-4 h-4 text-slate-400 group-focus-within:text-blue-500 transition-colors" />
                  Description
                </label>
                <textarea
                  name="description"
                  required
                  rows="4"
                  value={formData.description}
                  onChange={handleChange}
                  placeholder="Provide detailed information about your complaint..."
                  className="w-full px-4 py-3.5 bg-white/80 border border-slate-200 rounded-xl focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 outline-none transition-all duration-300 shadow-sm hover:bg-white placeholder:text-slate-400 text-slate-800 font-medium resize-none"
                ></textarea>
              </div>

              <div className="space-y-1.5 group">
                <label className="text-sm font-semibold text-slate-700 flex items-center gap-2 ml-1">
                  <MapPin className="w-4 h-4 text-slate-400 group-focus-within:text-blue-500 transition-colors" />
                  District / Location
                </label>
                <input
                  type="text"
                  name="district"
                  required
                  value={formData.district}
                  onChange={handleChange}
                  placeholder="e.g., Downtown, North District"
                  className="w-full px-4 py-3.5 bg-white/80 border border-slate-200 rounded-xl focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 outline-none transition-all duration-300 shadow-sm hover:bg-white placeholder:text-slate-400 text-slate-800 font-medium"
                />
              </div>

              <button 
                type="submit" 
                className="group w-full flex items-center justify-center gap-2 py-4 mt-8 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-lg font-bold rounded-xl shadow-lg shadow-blue-500/25 hover:shadow-xl hover:shadow-blue-500/40 hover:-translate-y-0.5 transition-all duration-300 active:scale-[0.98] active:translate-y-0"
              >
                Submit Complaint
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform duration-300" />
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default Home;
