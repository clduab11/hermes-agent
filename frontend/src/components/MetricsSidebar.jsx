import React, { useEffect, useState } from 'react';

const SLA_URL = import.meta.env.VITE_SLA_URL || 'http://localhost:8000/sla';

export default function MetricsSidebar() {
  const [sla, setSla] = useState({
    uptime: { target_percent: 99.9, current_percent: 0 },
    latency: { request_average_ms: 0, voice_pipeline_average_ms: 0 },
    voice_pipeline: { interactions_processed: 0 },
    active_connections: 0
  });
  const [lastUpdated, setLastUpdated] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    const fetchSla = async () => {
      try {
        const response = await fetch(SLA_URL, { cache: 'no-store' });
        if (!response.ok) {
          throw new Error(`SLA endpoint returned ${response.status}`);
        }
        const data = await response.json();
        if (!cancelled) {
          setSla(data);
          setLastUpdated(new Date());
          setError(null);
        }
      } catch (err) {
        console.warn('Falling back to demo SLA metrics:', err);
        if (!cancelled) {
          setError('Live SLA data unavailable. Showing demo metrics.');
          setSla((prev) => ({
            ...prev,
            uptime: { target_percent: 99.9, current_percent: 99.2 },
            latency: { request_average_ms: 180, voice_pipeline_average_ms: 95 },
            voice_pipeline: { interactions_processed: 2400 },
            active_connections: 5
          }));
        }
      }
    };

    fetchSla();
    const id = setInterval(fetchSla, 15000);

    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  return (
    <aside style={{ width: '260px', borderLeft: '1px solid #e5e7eb', padding: '1.5rem', background: '#f9fafb' }}>
      <h3 style={{ marginBottom: '.75rem' }}>SLA Snapshot</h3>
      <div style={{ fontSize: '0.95rem', lineHeight: '1.6' }}>
        <p><strong>Uptime Target:</strong> {sla.uptime.target_percent}%</p>
        <p><strong>Current Uptime:</strong> {sla.uptime.current_percent}%</p>
        <p><strong>API Latency:</strong> {sla.latency.request_average_ms} ms</p>
        <p><strong>Voice Pipeline Latency:</strong> {sla.latency.voice_pipeline_average_ms} ms</p>
        <p><strong>Interactions Processed:</strong> {sla.voice_pipeline?.interactions_processed ?? 0}</p>
        <p><strong>Live Connections:</strong> {sla.active_connections}</p>
        {lastUpdated && (
          <p style={{ fontSize: '0.8rem', color: '#6b7280' }}>
            Updated {lastUpdated.toLocaleTimeString()}
          </p>
        )}
        {error && (
          <p style={{ color: '#b45309', fontSize: '0.8rem', marginTop: '.5rem' }}>{error}</p>
        )}
      </div>
    </aside>
  );
}
