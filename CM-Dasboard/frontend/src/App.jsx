import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import RoleRoute from './components/RoleRoute';

// Layout
import DashboardLayout from './layouts/DashboardLayout';

// Admin Pages
import AdminDashboard from './pages/admin/AdminDashboard';
import AdminAnalytics from './pages/admin/AdminAnalytics';
import ComplaintsList from './pages/officer/ComplaintsList';
import ComplaintDetail from './pages/officer/ComplaintDetail';

// Citizen Pages
import CitizenDashboard from './pages/CitizenDashboard';
import Home from './pages/Home';
import Track from './pages/Track';
import Feedback from './pages/Feedback';

import Login from './pages/Login';
import Signup from './pages/Signup';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router>
          <Routes>
            <Route path="/" element={<Navigate to="/login" replace />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            
            {/* Citizen Routes */}
            <Route path="/dashboard" element={
              <RoleRoute allowedRoles={['citizen']}>
                <DashboardLayout />
              </RoleRoute>
            }>
              <Route index element={<CitizenDashboard />} />
              <Route path="submit" element={<Home />} />
              <Route path="track" element={<Track />} />
              <Route path="feedback" element={<Feedback />} />
            </Route>

            {/* Admin Routes */}
            <Route path="/admin" element={
              <RoleRoute allowedRoles={['admin']}>
                <DashboardLayout />
              </RoleRoute>
            }>
              <Route index element={<AdminDashboard />} />
              <Route path="analytics" element={<AdminAnalytics />} />
              <Route path="complaints" element={<ComplaintsList />} />
              <Route path="complaints/:id" element={<ComplaintDetail />} />
            </Route>
          </Routes>
        </Router>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
