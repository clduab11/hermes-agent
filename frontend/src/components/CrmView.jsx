import React, { useEffect, useState } from 'react';
import { io } from 'socket.io-client';

const socket = io();

export default function CrmView({ scenario }) {
  const [events, setEvents] = useState([]);
  useEffect(() => {
    socket.on('crm-event', evt => setEvents(prev => [...prev, evt]));
    return () => socket.off('crm-event');
  }, []);
  return (
    <div style={{ flex: 1, padding: '1rem' }}>
      <h2>CRM Updates</h2>
      <p>Scenario: {scenario}</p>
      <ul>
        {events.map((e, idx) => (
          <li key={idx}>{e}</li>
        ))}
      </ul>
    </div>
  );
}
