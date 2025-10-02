/**
 * Metrics Card Component
 * Copyright (c) 2025 Parallax Analytics LLC. All rights reserved.
 */

import React from 'react';

export default function MetricsCard({ title, value, subtitle, icon, trend }) {
  const trendIcon = trend === 'up' ? '📈' : trend === 'down' ? '📉' : '';

  return (
    <div className="card bg-base-100 shadow-xl">
      <div className="card-body">
        <div className="flex justify-between items-start">
          <h2 className="card-title text-lg">{title}</h2>
          <span className="text-3xl">{icon}</span>
        </div>
        <div className="mt-2">
          <div className="text-3xl font-bold">{value}</div>
          <div className="text-sm text-base-content/70 mt-1">
            {trendIcon} {subtitle}
          </div>
        </div>
      </div>
    </div>
  );
}
