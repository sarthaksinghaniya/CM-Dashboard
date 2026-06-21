import React from 'react';
import { Filter } from 'lucide-react';

const FilterBar = ({ statusFilter, setStatusFilter, districtFilter, setDistrictFilter }) => {
  return (
    <div className="flex flex-col sm:flex-row gap-4 items-center justify-between bg-white p-4 rounded-xl border border-slate-200 shadow-sm mb-6">
      <div className="flex items-center gap-2 text-slate-700 font-medium w-full sm:w-auto">
        <Filter className="w-4 h-4 text-slate-400" />
        <span>Filters</span>
      </div>

      <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-slate-50 border border-slate-200 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block p-2 text-slate-700 outline-none w-full sm:w-auto min-w-[140px]"
        >
          <option value="all">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="in progress">In Progress</option>
          <option value="resolved">Resolved</option>
        </select>

        <select
          value={districtFilter}
          onChange={(e) => setDistrictFilter(e.target.value)}
          className="bg-slate-50 border border-slate-200 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block p-2 text-slate-700 outline-none w-full sm:w-auto min-w-[140px]"
        >
          <option value="all">All Districts</option>
          <option value="downtown">Downtown</option>
          <option value="north district">North District</option>
          <option value="south district">South District</option>
        </select>
      </div>
    </div>
  );
};

export default FilterBar;
