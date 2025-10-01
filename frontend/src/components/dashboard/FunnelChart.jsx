/**
 * Funnel Chart Component
 * Copyright (c) 2025 Parallax Analytics LLC. All rights reserved.
 */

import React from 'react';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

export default function FunnelChart({ data }) {
  if (!data) {
    return <div className="text-center text-base-content/70">No data available</div>;
  }

  const chartData = {
    labels: ['Total Leads', 'Contacted', 'Qualified', 'Demo', 'Proposal', 'Won'],
    datasets: [
      {
        label: 'Lead Count',
        data: [
          data.total_leads || 0,
          data.contacted || 0,
          data.qualified || 0,
          data.demo_scheduled || 0,
          data.proposal_sent || 0,
          data.won || 0,
        ],
        backgroundColor: [
          'rgba(59, 130, 246, 0.5)',
          'rgba(147, 51, 234, 0.5)',
          'rgba(236, 72, 153, 0.5)',
          'rgba(251, 146, 60, 0.5)',
          'rgba(34, 197, 94, 0.5)',
          'rgba(16, 185, 129, 0.5)',
        ],
        borderColor: [
          'rgb(59, 130, 246)',
          'rgb(147, 51, 234)',
          'rgb(236, 72, 153)',
          'rgb(251, 146, 60)',
          'rgb(34, 197, 94)',
          'rgb(16, 185, 129)',
        ],
        borderWidth: 2,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  return (
    <div style={{ height: '300px' }}>
      <Bar data={chartData} options={options} />
    </div>
  );
}
