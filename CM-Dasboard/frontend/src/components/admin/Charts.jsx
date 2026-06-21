import React, { useMemo } from 'react';
import {
  PieChart, Pie, Cell, Tooltip as PieTooltip, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as BarTooltip, ResponsiveContainer,
  LineChart, Line
} from 'recharts';

const COLORS = ['#f59e0b', '#0ea5e9', '#10b981']; // amber for pending, blue for in progress, emerald for resolved

const Charts = ({ complaints }) => {
  
  // Transform data for Pie Chart (Status)
  const statusData = useMemo(() => {
    const counts = { pending: 0, 'in progress': 0, resolved: 0 };
    complaints.forEach(c => {
      const status = (c.status || 'pending').toLowerCase();
      if (counts[status] !== undefined) {
        counts[status]++;
      }
    });
    return [
      { name: 'Pending', value: counts.pending },
      { name: 'In Progress', value: counts['in progress'] },
      { name: 'Resolved', value: counts.resolved },
    ];
  }, [complaints]);

  // Transform data for Bar Chart (District)
  const districtData = useMemo(() => {
    const districtCounts = {};
    complaints.forEach(c => {
      const dist = c.district || c.location || 'Unknown';
      districtCounts[dist] = (districtCounts[dist] || 0) + 1;
    });
    return Object.keys(districtCounts).map(key => ({
      name: key,
      count: districtCounts[key]
    })).sort((a, b) => b.count - a.count).slice(0, 10); // top 10
  }, [complaints]);

  // Transform data for Line Chart (Monthly Trend)
  const monthlyData = useMemo(() => {
    const monthCounts = {};
    complaints.forEach(c => {
      const date = c.created_at ? new Date(c.created_at) : new Date();
      // Format as 'Jan', 'Feb', etc.
      const month = date.toLocaleString('default', { month: 'short' });
      monthCounts[month] = (monthCounts[month] || 0) + 1;
    });
    // Ensure chronological order could be complex without year, but for demo we just show available months
    const monthsOrder = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return Object.keys(monthCounts)
      .map(key => ({ name: key, count: monthCounts[key] }))
      .sort((a, b) => monthsOrder.indexOf(a.name) - monthsOrder.indexOf(b.name));
  }, [complaints]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      
      {/* Status Pie Chart */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/60 shadow-[0_2px_10px_rgb(0,0,0,0.02)] hover:shadow-[0_8px_30px_rgb(0,0,0,0.06)] transition-all duration-300">
        <h3 className="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-blue-500"></span>
          Complaints by Status
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={statusData}
                cx="50%"
                cy="50%"
                innerRadius={65}
                outerRadius={85}
                paddingAngle={6}
                dataKey="value"
                stroke="none"
              >
                {statusData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <PieTooltip 
                contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 20px rgba(0,0,0,0.08)', fontWeight: 500 }}
              />
              <Legend iconType="circle" wrapperStyle={{ fontSize: '13px', fontWeight: 500 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* District Bar Chart */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/60 shadow-[0_2px_10px_rgb(0,0,0,0.02)] hover:shadow-[0_8px_30px_rgb(0,0,0,0.06)] transition-all duration-300">
        <h3 className="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-indigo-500"></span>
          Complaints by District
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={districtData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b', fontWeight: 500 }} dy={10} />
              <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b', fontWeight: 500 }} />
              <BarTooltip 
                cursor={{ fill: '#f8fafc' }} 
                contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 20px rgba(0,0,0,0.08)' }}
              />
              <Bar dataKey="count" fill="#4f46e5" radius={[6, 6, 6, 6]} barSize={36} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Monthly Trend Line Chart */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/60 shadow-[0_2px_10px_rgb(0,0,0,0.02)] hover:shadow-[0_8px_30px_rgb(0,0,0,0.06)] transition-all duration-300 lg:col-span-2">
        <h3 className="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
          Monthly Trend
        </h3>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={monthlyData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b', fontWeight: 500 }} dy={10} />
              <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b', fontWeight: 500 }} />
              <BarTooltip 
                contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 20px rgba(0,0,0,0.08)' }}
              />
              <Line 
                type="monotone" 
                dataKey="count" 
                stroke="#10b981" 
                strokeWidth={3} 
                dot={{ r: 4, strokeWidth: 2, fill: '#fff', stroke: '#10b981' }} 
                activeDot={{ r: 6, strokeWidth: 0, fill: '#10b981', stroke: 'rgba(16, 185, 129, 0.3)', strokeWidth: 8 }} 
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

    </div>
  );
};

export default Charts;
