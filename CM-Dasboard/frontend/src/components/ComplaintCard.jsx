import React from 'react';
import StatusBadge from './StatusBadge';
import { MapPin, Calendar, User } from 'lucide-react';

const ComplaintCard = ({ complaint, onUpdateStatus }) => {
  return (
    <div className="glass-panel p-6 hover:shadow-xl transition-all group">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-bold text-slate-800 group-hover:text-primary-600 transition-colors">
            {complaint.title || 'Untitled Complaint'}
          </h3>
          <p className="text-sm text-slate-500 font-medium">Ticket ID: #{complaint.id || complaint.ticket_id}</p>
        </div>
        <StatusBadge status={complaint.status} />
      </div>
      
      <p className="text-slate-600 text-sm mb-4 line-clamp-2">
        {complaint.description}
      </p>
      
      <div className="flex items-center gap-4 text-xs text-slate-500 mb-4">
        <div className="flex items-center gap-1">
          <MapPin className="w-3.5 h-3.5" />
          {complaint.district || 'Unspecified'}
        </div>
        {complaint.created_at && (
          <div className="flex items-center gap-1">
            <Calendar className="w-3.5 h-3.5" />
            {new Date(complaint.created_at).toLocaleDateString()}
          </div>
        )}
        {complaint.assigned_officer && (
          <div className="flex items-center gap-1">
            <User className="w-3.5 h-3.5" />
            {complaint.assigned_officer}
          </div>
        )}
      </div>

      {onUpdateStatus && complaint.status?.toLowerCase() !== 'resolved' && (
        <div className="pt-4 border-t border-slate-100 flex gap-2">
          <button
            onClick={() => onUpdateStatus(complaint.id, 'In Progress')}
            className="btn-secondary text-xs px-3 py-1.5"
          >
            Mark In Progress
          </button>
          <button
            onClick={() => onUpdateStatus(complaint.id, 'Resolved')}
            className="btn-primary text-xs px-3 py-1.5"
          >
            Resolve
          </button>
        </div>
      )}
    </div>
  );
};

export default ComplaintCard;
