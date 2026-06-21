import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

// Layout
import DashboardLayout from './layouts/DashboardLayout';

// Pages
import AdminDashboard from './pages/admin/AdminDashboard';
import AdminAnalytics from './pages/admin/AdminAnalytics';
import Home from './pages/Home';
import Track from './pages/Track';
import Feedback from './pages/Feedback';

// Officer Pages (kept for full functionality)
import ComplaintsList from './pages/officer/ComplaintsList';
import ComplaintDetail from './pages/officer/ComplaintDetail';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          <Route element={<DashboardLayout />}>
            <Route path="/" element={<AdminDashboard />} />
            <Route path="/submit" element={<Home />} />
            <Route path="/track" element={<Track />} />
            <Route path="/feedback" element={<Feedback />} />
            <Route path="/analytics" element={<AdminAnalytics />} />
            
            {/* Maintained for officer/admin functionality */}
            <Route path="/complaints" element={<ComplaintsList />} />
            <Route path="/complaints/:id" element={<ComplaintDetail />} />
          </Route>
        </Routes>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
