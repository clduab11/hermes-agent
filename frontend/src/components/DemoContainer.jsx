import React from 'react';
import ConversationView from './ConversationView.jsx';
import CrmView from './CrmView.jsx';
import MetricsSidebar from './MetricsSidebar.jsx';

export default function DemoContainer({ scenario }) {
  return (
    <div className="demo-container" style={{ display: 'flex', height: '400px' }}>
      <ConversationView scenario={scenario} />
      <CrmView scenario={scenario} />
      <MetricsSidebar />
    </div>
  );
}
