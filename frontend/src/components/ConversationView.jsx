import React, { useEffect, useRef, useState } from 'react';
import useWebRTC from '../hooks/useWebRTC.js';

export default function ConversationView({ scenario }) {
  const { start, stop, transcript, phase, volume } = useWebRTC();
  const canvasRef = useRef(null);

  useEffect(() => {
    const ctx = canvasRef.current.getContext('2d');
    ctx.clearRect(0, 0, 300, 50);
    ctx.fillStyle = '#4caf50';
    const width = Math.min(volume * 300, 300);
    ctx.fillRect(0, 0, width, 50);
  }, [volume]);

  return (
    <div style={{ flex: 1, borderRight: '1px solid #ddd', padding: '1rem' }}>
      <h2>Conversation</h2>
      <p>Scenario: {scenario}</p>
      <div>
        <button onClick={start}>Start</button>
        <button onClick={stop}>Stop</button>
      </div>
      <div>Phase: {phase}</div>
      <canvas ref={canvasRef} width="300" height="50" />
      <pre style={{ whiteSpace: 'pre-wrap' }}>{transcript}</pre>
    </div>
  );
}
