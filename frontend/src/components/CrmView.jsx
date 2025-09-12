import React, { useEffect, useRef, useState } from 'react';
import { io } from 'socket.io-client';

const SOCKET_IO_URL = import.meta.env.VITE_SOCKET_IO_URL || 'http://localhost:3001';
const socket = io(SOCKET_IO_URL);

export default function CrmView({ scenario }) {
  const [events, setEvents] = useState([]);
  const idRef = useRef(0);
  useEffect(() => {
    const handler = evt => {
      setEvents(prev => [...prev, { id: idRef.current++, text: evt }]);
    };
    socket.on('crm-event', handler);
    return () => socket.off('crm-event', handler);
  }, []);
  return (
    <div style={{ flex: 1, padding: '1rem' }}>
      <h2>CRM Updates</h2>
      <p>Scenario: {scenario}</p>
      <ul>
        {events.map(e => (
          <li key={e.id}>{e.text}</li>
        ))}
      </ul>
    </div>
  );
}
