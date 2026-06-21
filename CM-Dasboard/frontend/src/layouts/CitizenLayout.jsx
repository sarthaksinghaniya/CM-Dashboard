import React from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from '../components/Navbar';

const CitizenLayout = () => {
  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  );
};

export default CitizenLayout;
