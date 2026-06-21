import React, { useState, useEffect } from 'react';
import { getOfficerComplaints } from '../../services/api';
import Charts from '../../components/admin/Charts';
import Loader from '../../components/Loader';
import { BarChart3 } from 'lucide-react';

const AdminAnalytics = () => {
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
      console.error('Failed to fetch analytics data', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="py-20"><Loader /></div>;
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-indigo-100 text-indigo-600 rounded-lg">
          <BarChart3 className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Analytics & Insights</h1>
          <p className="text-sm text-slate-500 mt-1">Deep dive into complaint data, demographics, and trends.</p>
        </div>
      </div>

      {/* Reusing the Charts component, but here it takes full focus */}
      <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200">
        <Charts complaints={complaints} />
      </div>

      <div className="bg-white p-8 rounded-xl border border-slate-200 shadow-sm text-center">
        <h3 className="text-lg font-bold text-slate-700 mb-2">Performance Metrics</h3>
        <p className="text-slate-500">Advanced ML-driven analytics and officer performance metrics will be displayed here in future updates.</p>
      </div>
    </div>
  );
};

export default AdminAnalytics;
