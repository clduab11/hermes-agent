import React, { useEffect, useState } from 'react';

export default function MetricsSidebar() {
  const [seconds, setSeconds] = useState(0);
  const [cost, setCost] = useState(0);
  const [calls, setCalls] = useState(42);

  useEffect(() => {
    const id = setInterval(() => {
      setSeconds(s => s + 1);
      setCost(c => c + 0.05);
    }, 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <div style={{ width: '200px', borderLeft: '1px solid #ddd', padding: '1rem' }}>
      <h3>Metrics</h3>
      <p>Time Saved: {seconds}s</p>
      <p>Cost Savings: ${cost.toFixed(2)}</p>
      <p>Calls handled today: {calls}</p>
    </div>
  );
}
