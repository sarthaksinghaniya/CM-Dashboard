import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

// Layouts
import CitizenLayout from './layouts/CitizenLayout';
import DashboardLayout from './layouts/DashboardLayout';

// Citizen Pages
import Home from './pages/Home';
import Track from './pages/Track';
import Feedback from './pages/Feedback';

// Officer Pages
import ComplaintsList from './pages/officer/ComplaintsList';
import ComplaintDetail from './pages/officer/ComplaintDetail';

// Admin Pages
import AdminDashboard from './pages/admin/AdminDashboard';
import AdminAnalytics from './pages/admin/AdminAnalytics';

function App() {
  return (
    <Router>
      <Routes>
        {/* Citizen UI Routes */}
        <Route element={<CitizenLayout />}>
          <Route path="/" element={<Home />} />
          <Route path="/track" element={<Track />} />
          <Route path="/feedback" element={<Feedback />} />
        </Route>

        {/* Officer Dashboard Routes */}
        <Route path="/officer" element={<DashboardLayout />}>
          <Route index element={<ComplaintsList />} />
          <Route path=":id" element={<ComplaintDetail />} />
        </Route>

        {/* Admin Dashboard Routes */}
        <Route path="/admin" element={<DashboardLayout />}>
          <Route index element={<AdminDashboard />} />
          <Route path="complaints" element={<ComplaintsList />} />
          <Route path="analytics" element={<AdminAnalytics />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
