/**
 * Dashboard Layout Component
 * Copyright (c) 2025 Parallax Analytics LLC. All rights reserved.
 */

import React from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';

export default function DashboardLayout() {
  const location = useLocation();

  const navItems = [
    { path: '/dashboard', label: '📊 Overview', exact: true },
    { path: '/dashboard/leads', label: '🎯 Leads' },
    { path: '/dashboard/social', label: '📱 Social Media' },
    { path: '/dashboard/analytics', label: '📈 Analytics' },
    { path: '/dashboard/technical', label: '⚙️ Technical Docs' },
  ];

  const isActive = (item) => {
    if (item.exact) {
      return location.pathname === item.path;
    }
    return location.pathname.startsWith(item.path);
  };

  return (
    <div className="min-h-screen bg-base-200">
      {/* Header */}
      <div className="navbar bg-primary text-primary-content">
        <div className="flex-1">
          <Link to="/" className="btn btn-ghost normal-case text-xl">
            🏛️ HERMES Marketing Command Center
          </Link>
        </div>
        <div className="flex-none">
          <Link to="/" className="btn btn-ghost">
            Back to Home
          </Link>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="tabs tabs-boxed justify-center bg-base-100 p-4">
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`tab tab-lg ${isActive(item) ? 'tab-active' : ''}`}
          >
            {item.label}
          </Link>
        ))}
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        <Outlet />
      </div>
    </div>
  );
}
