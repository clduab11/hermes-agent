import React, { useState } from 'react';
import DemoContainer from './components/DemoContainer.jsx';
import RoiCalculator from './components/RoiCalculator.jsx';
import Testimonials from './components/Testimonials.jsx';
import PartnerLogos from './components/PartnerLogos.jsx';

export default function App() {
  const [scenario, setScenario] = useState(null);
  const SCENARIOS = {
    INTAKE: 'intake',
    EMERGENCY: 'emergency',
    BILLING: 'billing',
    COURT: 'court'
  };
  return (
    <div className="app">
      <h1>Hermes Voice AI Demo</h1>
      <div className="scenario-buttons">
        <button onClick={() => setScenario(SCENARIOS.INTAKE)}>Car Accident Intake</button>
        <button onClick={() => setScenario(SCENARIOS.EMERGENCY)}>2 AM Arrest</button>
        <button onClick={() => setScenario(SCENARIOS.BILLING)}>Invoice Question</button>
        <button onClick={() => setScenario(SCENARIOS.COURT)}>Court Reminder</button>
      </div>
      {scenario && <DemoContainer scenario={scenario} />}
      <RoiCalculator />
      <Testimonials />
      <PartnerLogos />
    </div>
  );
}
