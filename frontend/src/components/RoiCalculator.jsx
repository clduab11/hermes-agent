import React, { useState } from 'react';

export default function RoiCalculator() {
  const [hours, setHours] = useState(10);
  const [rate, setRate] = useState(200);

  const savings = hours * rate * 0.3; // simple demo formula

  return (
    <div className="roi-calculator" style={{ marginTop: '2rem' }}>
      <h2>ROI Calculator</h2>
      <label>Hours saved per week: <input type="number" value={hours} onChange={e => setHours(+e.target.value)} /></label>
      <label>Hourly rate ($): <input type="number" value={rate} onChange={e => setRate(+e.target.value)} /></label>
      <p>Estimated Monthly Savings: ${savings.toFixed(2)}</p>
    </div>
  );
}
