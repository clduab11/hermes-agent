/**
 * Dashboard Overview Component
 * Copyright (c) 2025 Parallax Analytics LLC. All rights reserved.
 */

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '../../services/api';
import MetricsCard from './MetricsCard';
import FunnelChart from './FunnelChart';

export default function DashboardOverview() {
  const { data: metrics, isLoading, error } = useQuery({
    queryKey: ['dashboardMetrics'],
    queryFn: async () => {
      const response = await analyticsApi.getMetrics();
      return response.data;
    },
  });

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <span className="loading loading-spinner loading-lg"></span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-error">
        <span>Error loading dashboard metrics: {error.message}</span>
      </div>
    );
  }

  const { funnel, pipeline, social, roi } = metrics || {};

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Marketing Command Center</h1>

      {/* Key Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricsCard
          title="Total Leads"
          value={funnel?.total_leads || 0}
          subtitle={`${funnel?.conversion_rate || 0}% conversion rate`}
          icon="🎯"
          trend="up"
        />
        <MetricsCard
          title="Pipeline Value"
          value={`$${((pipeline?.total_pipeline_value || 0) / 1000).toFixed(0)}K`}
          subtitle={`${pipeline?.active_opportunities || 0} active opportunities`}
          icon="💰"
          trend="up"
        />
        <MetricsCard
          title="Social Posts"
          value={social?.total_posts || 0}
          subtitle={`${social?.engagement_rate || 0}% engagement rate`}
          icon="📱"
        />
        <MetricsCard
          title="Annual ROI"
          value={`$${((roi?.annual_savings || 0) / 1000).toFixed(0)}K`}
          subtitle="Cost savings projected"
          icon="📈"
          trend="up"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card bg-base-100 shadow-xl">
          <div className="card-body">
            <h2 className="card-title">Conversion Funnel</h2>
            <FunnelChart data={funnel} />
          </div>
        </div>

        <div className="card bg-base-100 shadow-xl">
          <div className="card-body">
            <h2 className="card-title">Pipeline Breakdown</h2>
            <div className="space-y-4">
              <div className="stat">
                <div className="stat-title">Qualified Leads</div>
                <div className="stat-value text-primary">{funnel?.qualified || 0}</div>
              </div>
              <div className="stat">
                <div className="stat-title">Demo Scheduled</div>
                <div className="stat-value text-secondary">{funnel?.demo_scheduled || 0}</div>
              </div>
              <div className="stat">
                <div className="stat-title">Won Deals</div>
                <div className="stat-value text-success">{funnel?.won || 0}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ROI Calculator */}
      <div className="card bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-xl">
        <div className="card-body">
          <h2 className="card-title text-2xl">ROI Impact</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
            <div>
              <div className="text-sm opacity-90">Monthly Revenue</div>
              <div className="text-3xl font-bold">${((roi?.monthly_revenue || 0) / 1000).toFixed(1)}K</div>
            </div>
            <div>
              <div className="text-sm opacity-90">Annual Savings</div>
              <div className="text-3xl font-bold">${((roi?.annual_savings || 0) / 1000).toFixed(1)}K</div>
            </div>
            <div>
              <div className="text-sm opacity-90">Leads Processed</div>
              <div className="text-3xl font-bold">{roi?.total_leads_processed || 0}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
