import React, { useState } from 'react';

export default function RoiCalculator() {
  const [attorneys, setAttorneys] = useState(5);
  const [hourlyRate, setHourlyRate] = useState(300);
  const [currentMissedCalls, setCurrentMissedCalls] = useState(15);
  const [adminHours, setAdminHours] = useState(20);

  // ROI Calculations based on README metrics
  const missedCallsImprovement = currentMissedCalls * 0.85; // 85% improvement
  const adminReduction = adminHours * 0.5; // 40-60% reduction (using 50% average)
  const productivityIncrease = attorneys * 5; // 20-35% more billable hours (using 5 hours average per attorney)
  
  const monthlyMissedCallRevenue = missedCallsImprovement * 4 * 500; // Assuming $500 average per missed call opportunity
  const monthlyAdminSavings = adminReduction * 4 * hourlyRate;
  const monthlyProductivityGains = productivityIncrease * 4 * hourlyRate;
  
  const totalMonthlySavings = monthlyMissedCallRevenue + monthlyAdminSavings + monthlyProductivityGains;
  const annualSavings = totalMonthlySavings * 12;
  
  // Professional tier cost: $2,497/month
  const professionalTierCost = 2497;
  const roiMonthly = totalMonthlySavings - professionalTierCost;
  const roiPercentage = ((totalMonthlySavings - professionalTierCost) / professionalTierCost) * 100;

  const styles = {
    calculator: {
      background: 'white',
      padding: '2.5rem',
      borderRadius: '15px',
      boxShadow: '0 8px 25px rgba(0,0,0,0.1)',
      border: '1px solid #e5e7eb'
    },
    title: {
      fontSize: '2rem',
      textAlign: 'center',
      marginBottom: '2rem',
      color: '#1f2937'
    },
    inputGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
      gap: '1.5rem',
      marginBottom: '2rem'
    },
    inputGroup: {
      display: 'flex',
      flexDirection: 'column'
    },
    label: {
      fontWeight: 'bold',
      marginBottom: '0.5rem',
      color: '#374151'
    },
    input: {
      padding: '0.75rem',
      border: '2px solid #e5e7eb',
      borderRadius: '8px',
      fontSize: '1rem',
      transition: 'border-color 0.3s ease'
    },
    resultsGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
      gap: '1rem',
      marginTop: '2rem'
    },
    resultCard: {
      background: '#f0f9ff',
      padding: '1.5rem',
      borderRadius: '10px',
      textAlign: 'center',
      border: '1px solid #0ea5e9'
    },
    resultValue: {
      fontSize: '1.5rem',
      fontWeight: 'bold',
      color: '#0369a1',
      marginBottom: '0.5rem'
    },
    resultLabel: {
      fontSize: '0.9rem',
      color: '#6b7280'
    },
    totalROI: {
      background: roiMonthly > 0 ? '#10b981' : '#ef4444',
      color: 'white',
      padding: '2rem',
      borderRadius: '10px',
      textAlign: 'center',
      marginTop: '2rem'
    },
    breakdown: {
      background: '#f8fafc',
      padding: '1.5rem',
      borderRadius: '10px',
      marginTop: '2rem'
    }
  };

  return (
    <div style={styles.calculator}>
      <h2 style={styles.title}>💰 HERMES ROI Calculator</h2>
      <p style={{ textAlign: 'center', color: '#6b7280', marginBottom: '2rem' }}>
        Calculate your firm's potential return on investment with HERMES
      </p>
      
      <div style={styles.inputGrid}>
        <div style={styles.inputGroup}>
          <label style={styles.label}>Number of Attorneys</label>
          <input
            type="number"
            min="1"
            value={attorneys}
            onChange={(e) => setAttorneys(parseInt(e.target.value) || 1)}
            style={styles.input}
          />
        </div>
        <div style={styles.inputGroup}>
          <label style={styles.label}>Average Hourly Rate ($)</label>
          <input
            type="number"
            min="100"
            value={hourlyRate}
            onChange={(e) => setHourlyRate(parseInt(e.target.value) || 100)}
            style={styles.input}
          />
        </div>
        <div style={styles.inputGroup}>
          <label style={styles.label}>Missed Calls Per Week</label>
          <input
            type="number"
            min="0"
            value={currentMissedCalls}
            onChange={(e) => setCurrentMissedCalls(parseInt(e.target.value) || 0)}
            style={styles.input}
          />
        </div>
        <div style={styles.inputGroup}>
          <label style={styles.label}>Admin Hours Per Week</label>
          <input
            type="number"
            min="0"
            value={adminHours}
            onChange={(e) => setAdminHours(parseInt(e.target.value) || 0)}
            style={styles.input}
          />
        </div>
      </div>

      <div style={styles.resultsGrid}>
        <div style={styles.resultCard}>
          <div style={styles.resultValue}>${monthlyMissedCallRevenue.toLocaleString()}</div>
          <div style={styles.resultLabel}>Monthly Recovered Revenue</div>
          <div style={{ fontSize: '0.8rem', marginTop: '0.5rem', color: '#6b7280' }}>
            (85% fewer missed opportunities)
          </div>
        </div>
        <div style={styles.resultCard}>
          <div style={styles.resultValue}>${monthlyAdminSavings.toLocaleString()}</div>
          <div style={styles.resultLabel}>Monthly Admin Savings</div>
          <div style={{ fontSize: '0.8rem', marginTop: '0.5rem', color: '#6b7280' }}>
            (50% overhead reduction)
          </div>
        </div>
        <div style={styles.resultCard}>
          <div style={styles.resultValue}>${monthlyProductivityGains.toLocaleString()}</div>
          <div style={styles.resultLabel}>Monthly Productivity Gains</div>
          <div style={{ fontSize: '0.8rem', marginTop: '0.5rem', color: '#6b7280' }}>
            (25% more billable hours)
          </div>
        </div>
        <div style={styles.resultCard}>
          <div style={styles.resultValue}>${annualSavings.toLocaleString()}</div>
          <div style={styles.resultLabel}>Total Annual Savings</div>
          <div style={{ fontSize: '0.8rem', marginTop: '0.5rem', color: '#6b7280' }}>
            (Before HERMES cost)
          </div>
        </div>
      </div>

      <div style={styles.totalROI}>
        <h3 style={{ margin: '0 0 1rem 0' }}>
          {roiMonthly > 0 ? '🎉' : '⚠️'} Monthly ROI Analysis
        </h3>
        <div style={{ fontSize: '2rem', fontWeight: 'bold', marginBottom: '1rem' }}>
          ${roiMonthly.toLocaleString()} / month
        </div>
        <div style={{ fontSize: '1.2rem', marginBottom: '1rem' }}>
          {roiPercentage > 0 ? '+' : ''}{roiPercentage.toFixed(1)}% ROI
        </div>
        <div style={{ fontSize: '0.9rem', opacity: '0.9' }}>
          {roiMonthly > 0 
            ? `HERMES pays for itself and generates ${Math.abs(roiMonthly).toLocaleString()} in additional monthly value`
            : 'Consider the Enterprise tier for larger practices or contact us for custom pricing'
          }
        </div>
      </div>

      <div style={styles.breakdown}>
        <h4 style={{ marginBottom: '1rem', color: '#374151' }}>📊 Savings Breakdown</h4>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '0.5rem', fontSize: '0.9rem' }}>
          <span>Total Monthly Benefits:</span>
          <span style={{ fontWeight: 'bold' }}>${totalMonthlySavings.toLocaleString()}</span>
          <span>HERMES Professional Cost:</span>
          <span style={{ fontWeight: 'bold', color: '#ef4444' }}>-${professionalTierCost.toLocaleString()}</span>
          <hr style={{ gridColumn: '1 / -1', margin: '0.5rem 0', border: 'none', borderTop: '1px solid #d1d5db' }} />
          <span style={{ fontWeight: 'bold' }}>Net Monthly ROI:</span>
          <span style={{ fontWeight: 'bold', color: roiMonthly > 0 ? '#10b981' : '#ef4444' }}>
            ${roiMonthly.toLocaleString()}
          </span>
        </div>
        <p style={{ fontSize: '0.8rem', color: '#6b7280', marginTop: '1rem', fontStyle: 'italic' }}>
          * Calculations based on industry averages and HERMES performance metrics. Individual results may vary. 
          Contact our legal technology specialists for a customized ROI analysis.
        </p>
      </div>
    </div>
  );
}
