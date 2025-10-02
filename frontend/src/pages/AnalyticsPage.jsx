/**
 * Analytics Page
 * Copyright (c) 2025 Parallax Analytics LLC. All rights reserved.
 */

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '../services/api';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

export default function AnalyticsPage() {
  const { data: metrics, isLoading } = useQuery({
    queryKey: ['analyticsMetrics'],
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

  const { funnel, pipeline, social, roi } = metrics || {};

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Marketing Analytics</h1>

      {/* ROI Section */}
      <div className="card bg-gradient-to-r from-green-500 to-blue-600 text-white shadow-xl">
        <div className="card-body">
          <h2 className="card-title text-2xl mb-4">Return on Investment</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div>
              <div className="text-sm opacity-90">Monthly Revenue</div>
              <div className="text-4xl font-bold">${((roi?.monthly_revenue || 0) / 1000).toFixed(1)}K</div>
              <div className="text-xs opacity-75 mt-1">from won deals</div>
            </div>
            <div>
              <div className="text-sm opacity-90">Annual Revenue</div>
              <div className="text-4xl font-bold">${((roi?.annual_revenue || 0) / 1000).toFixed(0)}K</div>
              <div className="text-xs opacity-75 mt-1">projected annually</div>
            </div>
            <div>
              <div className="text-sm opacity-90">Cost Savings</div>
              <div className="text-4xl font-bold">${((roi?.annual_savings || 0) / 1000).toFixed(0)}K</div>
              <div className="text-xs opacity-75 mt-1">per year</div>
            </div>
            <div>
              <div className="text-sm opacity-90">ROI Percentage</div>
              <div className="text-4xl font-bold">{roi?.roi_percentage || 0}%</div>
              <div className="text-xs opacity-75 mt-1">return rate</div>
            </div>
          </div>
        </div>
      </div>

      {/* Pipeline Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card bg-base-100 shadow-xl">
          <div className="card-body">
            <h2 className="card-title">Pipeline Overview</h2>
            <div className="space-y-4 mt-4">
              <div className="flex justify-between items-center">
                <span>Total Pipeline Value</span>
                <span className="text-2xl font-bold text-primary">
                  ${((pipeline?.total_pipeline_value || 0) / 1000).toFixed(0)}K
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span>Weighted Value</span>
                <span className="text-2xl font-bold text-secondary">
                  ${((pipeline?.weighted_pipeline_value || 0) / 1000).toFixed(0)}K
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span>Active Opportunities</span>
                <span className="text-2xl font-bold text-accent">
                  {pipeline?.active_opportunities || 0}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span>Average Win Probability</span>
                <span className="text-2xl font-bold">
                  {pipeline?.average_probability || 0}%
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="card bg-base-100 shadow-xl">
          <div className="card-body">
            <h2 className="card-title">Conversion Funnel</h2>
            <div className="space-y-3 mt-4">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm">Total Leads</span>
                  <span className="text-sm font-bold">{funnel?.total_leads || 0}</span>
                </div>
                <progress className="progress progress-primary w-full" value="100" max="100"></progress>
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm">Contacted</span>
                  <span className="text-sm font-bold">{funnel?.contacted || 0}</span>
                </div>
                <progress
                  className="progress progress-secondary w-full"
                  value={(funnel?.contacted || 0) / (funnel?.total_leads || 1) * 100}
                  max="100"
                ></progress>
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm">Qualified</span>
                  <span className="text-sm font-bold">{funnel?.qualified || 0}</span>
                </div>
                <progress
                  className="progress progress-accent w-full"
                  value={(funnel?.qualified || 0) / (funnel?.total_leads || 1) * 100}
                  max="100"
                ></progress>
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm">Won Deals</span>
                  <span className="text-sm font-bold">{funnel?.won || 0}</span>
                </div>
                <progress
                  className="progress progress-success w-full"
                  value={(funnel?.won || 0) / (funnel?.total_leads || 1) * 100}
                  max="100"
                ></progress>
              </div>
              <div className="mt-4 p-4 bg-base-200 rounded-lg">
                <div className="text-center">
                  <div className="text-sm opacity-70">Overall Conversion Rate</div>
                  <div className="text-3xl font-bold text-success">{funnel?.conversion_rate || 0}%</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Social Media Performance */}
      <div className="card bg-base-100 shadow-xl">
        <div className="card-body">
          <h2 className="card-title">Social Media Performance</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 mt-4">
            <div className="stat p-4">
              <div className="stat-title text-xs">Total Posts</div>
              <div className="stat-value text-2xl">{social?.total_posts || 0}</div>
            </div>
            <div className="stat p-4">
              <div className="stat-title text-xs">Published</div>
              <div className="stat-value text-2xl text-success">{social?.published || 0}</div>
            </div>
            <div className="stat p-4">
              <div className="stat-title text-xs">Impressions</div>
              <div className="stat-value text-2xl">{((social?.total_impressions || 0) / 1000).toFixed(1)}K</div>
            </div>
            <div className="stat p-4">
              <div className="stat-title text-xs">Engagements</div>
              <div className="stat-value text-2xl">{social?.total_engagements || 0}</div>
            </div>
            <div className="stat p-4">
              <div className="stat-title text-xs">Clicks</div>
              <div className="stat-value text-2xl">{social?.total_clicks || 0}</div>
            </div>
            <div className="stat p-4">
              <div className="stat-title text-xs">Engagement Rate</div>
              <div className="stat-value text-2xl">{social?.engagement_rate || 0}%</div>
            </div>
            <div className="stat p-4">
              <div className="stat-title text-xs">Click Rate</div>
              <div className="stat-value text-2xl">{social?.click_rate || 0}%</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
