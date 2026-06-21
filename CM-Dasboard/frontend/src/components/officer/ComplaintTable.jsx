import React from 'react';
import { useNavigate } from 'react-router-dom';
import StatusBadge from '../StatusBadge';
import { Eye } from 'lucide-react';

const ComplaintTable = ({ complaints }) => {
  const navigate = useNavigate();

  return (
    <div className="bg-white border border-slate-200/60 rounded-2xl shadow-[0_2px_10px_rgb(0,0,0,0.02)] overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-100">
          <thead className="bg-slate-50/50">
            <tr>
              <th scope="col" className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">
                ID
              </th>
              <th scope="col" className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">
                Description
              </th>
              <th scope="col" className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">
                District / Dept
              </th>
              <th scope="col" className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">
                Priority
              </th>
              <th scope="col" className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">
                Status
              </th>
              <th scope="col" className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">
                Created
              </th>
              <th scope="col" className="px-6 py-4 text-right text-xs font-bold text-slate-500 uppercase tracking-wider">
                Action
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-slate-100">
            {complaints.length > 0 ? (
              complaints.map((complaint) => (
                <tr key={complaint.id || complaint.ticket_id} className="hover:bg-slate-50/80 transition-colors group">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-slate-900">
                    #{complaint.ticket_id || complaint.id}
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm font-semibold text-slate-900 line-clamp-1">{complaint.title || 'Untitled'}</div>
                    <div className="text-sm text-slate-500 line-clamp-1 max-w-xs mt-0.5">{complaint.description}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-slate-800">{complaint.district || complaint.location || 'N/A'}</div>
                    <div className="text-xs text-slate-500 mt-0.5">{complaint.department || 'General'}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold uppercase tracking-wider
                      ${complaint.priority === 'high' ? 'bg-rose-50 text-rose-700 ring-1 ring-rose-600/20' : 
                        complaint.priority === 'medium' ? 'bg-amber-50 text-amber-700 ring-1 ring-amber-600/20' : 
                        'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-600/20'}`}>
                      {complaint.priority || 'Normal'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <StatusBadge status={complaint.status} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-500">
                    {complaint.created_at ? new Date(complaint.created_at).toLocaleDateString() : 'Just now'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => navigate(`/admin/complaints/${complaint.ticket_id || complaint.id}`)}
                      className="inline-flex items-center gap-1.5 px-3 py-2 bg-white border border-slate-200 text-slate-700 hover:text-indigo-600 hover:border-indigo-200 hover:bg-indigo-50 rounded-lg transition-all shadow-sm font-semibold opacity-0 group-hover:opacity-100 focus:opacity-100"
                    >
                      <Eye className="w-4 h-4" />
                      View
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="7" className="px-6 py-12 text-center text-slate-500 font-medium">
                  No complaints found matching the criteria.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ComplaintTable;
