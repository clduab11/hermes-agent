import React, { useEffect, useRef } from 'react';
import useWebRTC from '../hooks/useWebRTC.js';

export default function ConversationView({ scenario }) {
  const { start, stop, transcript, phase, volume, isConnected, isDemoMode } = useWebRTC();
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Different colors based on connection status
    if (isDemoMode) {
      ctx.fillStyle = '#ff9800'; // Orange for demo mode
    } else if (isConnected) {
      ctx.fillStyle = '#4caf50'; // Green for connected
    } else {
      ctx.fillStyle = '#f44336'; // Red for disconnected
    }
    
    const width = Math.min(volume * canvas.width, canvas.width);
    ctx.fillRect(0, 0, width, canvas.height);
  }, [volume, isConnected, isDemoMode]);

  const getScenarioDescription = (scenario) => {
    const scenarios = {
      intake: '🚗 Car Accident Intake - Client calling about recent accident',
      emergency: '🚨 2 AM Arrest Call - Urgent legal assistance needed',
      billing: '💳 Invoice Question - Client inquiry about billing',
      court: '⚖️ Court Reminder - Upcoming court date notification'
    };
    return scenarios[scenario] || `📞 General Legal Inquiry - ${scenario}`;
  };

  const getPhaseDisplay = (phase) => {
    const phases = {
      idle: '⏹️ Ready',
      connecting: '🔄 Connecting...',
      requesting_mic: '🎤 Requesting microphone access...',
      listening: '🎙️ Listening',
      demo_listening: '🎙️ Demo: Listening (frontend only)',
      demo_mode: '🔧 Demo Mode',
      stopping: '⏹️ Stopping...',
      error: '❌ Error',
    };
    return phases[phase] || phase;
  };

  const getButtonText = () => {
    if (phase === 'listening' || phase === 'demo_listening') {
      return 'Stop Recording';
    }
    return 'Start Voice Input';
  };

  const isActive = phase === 'listening' || phase === 'demo_listening';

  return (
    <div style={{ 
      flex: 1, 
      borderRight: '1px solid #ddd', 
      padding: '1rem',
      minHeight: '400px',
      display: 'flex',
      flexDirection: 'column'
    }}>
      <div style={{ marginBottom: '1rem' }}>
        <h3>🎙️ Voice Conversation</h3>
        <p style={{ 
          fontSize: '0.9rem', 
          color: '#666',
          margin: '0.5rem 0'
        }}>
          {getScenarioDescription(scenario)}
        </p>
        
        {isDemoMode && (
          <div style={{
            background: '#e3f2fd',
            border: '1px solid #2196f3',
            borderRadius: '8px',
            padding: '1rem',
            margin: '0.5rem 0',
            fontSize: '0.9rem'
          }}>
            <strong>🎭 Demo Mode Active</strong>
            <p style={{ margin: '0.5rem 0 0 0', lineHeight: '1.4' }}>
              This demonstrates the HERMES frontend interface. The microphone works and audio levels are visualized, 
              but voice transcription requires a backend server.
            </p>
            <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.85rem', opacity: 0.8 }}>
              💡 <strong>Want full functionality?</strong> See the deployment guide in the README to connect a backend server.
            </p>
          </div>
        )}
        
        {isConnected && (
          <div style={{
            background: '#e8f5e8',
            border: '1px solid #4caf50',
            borderRadius: '8px',
            padding: '1rem',
            margin: '0.5rem 0',
            fontSize: '0.9rem'
          }}>
            <strong>✅ Backend Connected</strong>
            <p style={{ margin: '0.5rem 0 0 0', lineHeight: '1.4' }}>
              Voice processing pipeline active. Speech will be transcribed and processed by AI for intelligent responses.
            </p>
          </div>
        )}
      </div>

      <div style={{ marginBottom: '1rem' }}>
        <button 
          onClick={isActive ? stop : start}
          style={{
            background: isActive ? '#f44336' : '#4caf50',
            color: 'white',
            border: 'none',
            padding: '0.75rem 1.5rem',
            borderRadius: '8px',
            fontSize: '1rem',
            cursor: 'pointer',
            marginRight: '0.5rem'
          }}
        >
          {getButtonText()}
        </button>
        
        <span style={{ 
          fontSize: '0.9rem', 
          color: '#666',
          marginLeft: '0.5rem'
        }}>
          {getPhaseDisplay(phase)}
        </span>
      </div>

      <div style={{ marginBottom: '1rem' }}>
        <div style={{ fontSize: '0.85rem', color: '#666', marginBottom: '0.5rem' }}>
          Audio Level:
        </div>
        <canvas 
          ref={canvasRef} 
          width="300" 
          height="20" 
          style={{ 
            border: '1px solid #ddd', 
            borderRadius: '4px',
            background: '#f5f5f5'
          }} 
        />
      </div>

      <div style={{ 
        flex: 1,
        background: '#f9f9f9',
        border: '1px solid #ddd',
        borderRadius: '8px',
        padding: '1rem',
        overflow: 'auto',
        fontFamily: 'monospace',
        fontSize: '0.9rem',
        lineHeight: '1.4'
      }}>
        {transcript || 'Voice transcript will appear here...'}
      </div>
    </div>
  );
}
