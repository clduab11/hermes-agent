import { useEffect, useRef, useState } from 'react';

export default function useWebRTC() {
  const mediaStream = useRef(null);
  const animationFrameId = useRef(null);
  const websocket = useRef(null);
  const mediaRecorder = useRef(null);
  const [transcript, setTranscript] = useState('');
  const [phase, setPhase] = useState('idle');
  const [volume, setVolume] = useState(0);
  const [isConnected, setIsConnected] = useState(false);

  // Get WebSocket URL from environment or default to localhost
  const getWebSocketUrl = () => {
    // Try to get from environment variable (for different deployment environments)
    const envUrl = import.meta.env.VITE_SOCKET_IO_URL;
    if (envUrl) {
      return envUrl.replace(/^https?:\/\//, '').replace(/\/$/, '');
    }
    
    // Default fallback for different environments
    if (window.location.hostname === 'clduab11.github.io') {
      // For GitHub Pages, we'll need to connect to a deployed backend
      // For now, show a demo mode message
      return null;
    } else if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      return 'localhost:8000';
    }
    
    return window.location.host;
  };

  const connectWebSocket = () => {
    const wsHost = getWebSocketUrl();
    if (!wsHost) {
      console.log('Running in demo mode - no backend connection available');
      setPhase('demo_mode');
      setTranscript('Demo mode: This is a frontend-only demonstration. For full functionality, connect to a HERMES backend server.');
      return false;
    }

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${wsHost}/ws/voice`;
      
      console.log(`Attempting to connect to WebSocket: ${wsUrl}`);
      websocket.current = new WebSocket(wsUrl);

      websocket.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setTranscript('Connected to HERMES voice assistant. Ready to process voice input.');
      };

      websocket.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleWebSocketMessage(message);
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      websocket.current.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        setPhase('idle');
        setTranscript('Disconnected from server. Click start to reconnect.');
      };

      websocket.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
        setPhase('error');
        setTranscript('Connection error. Running in demo mode. For full functionality, ensure HERMES backend is running.');
      };

      return true;
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setPhase('demo_mode');
      setTranscript('Demo mode: Backend connection not available. This demonstrates the frontend interface.');
      return false;
    }
  };

  const handleWebSocketMessage = (message) => {
    console.log('Received WebSocket message:', message);
    
    switch (message.type) {
      case 'connection_established':
        setTranscript('Connection established. Ready for voice input.');
        break;
      
      case 'transcription':
        setTranscript(`You said: "${message.text}" (${(message.confidence * 100).toFixed(1)}% confidence)`);
        break;
      
      case 'response':
        setTranscript(`HERMES: ${message.text}`);
        if (message.requires_human_transfer) {
          setTranscript(prev => prev + '\n⚠️ This inquiry requires human assistance.');
        }
        break;
      
      case 'error':
        setTranscript(`Error: ${message.message}`);
        setPhase('error');
        break;
      
      case 'metrics':
        console.log('Processing metrics:', message);
        break;
      
      default:
        console.log('Unknown message type:', message.type);
    }
  };

  const start = async () => {
    try {
      setPhase('connecting');
      setTranscript('Connecting to voice assistant...');

      // First establish WebSocket connection
      const connected = connectWebSocket();
      
      if (!connected) {
        // Demo mode - just show volume visualization
        setPhase('demo_listening');
        setTranscript('Demo mode: Microphone access granted. In a real deployment, this would send audio to HERMES for processing.');
      }

      // Get microphone access
      setPhase('requesting_mic');
      setTranscript('Requesting microphone access...');
      
      mediaStream.current = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true
        }
      });

      // Set up audio analysis for volume visualization
      const audioCtx = new AudioContext();
      const source = audioCtx.createMediaStreamSource(mediaStream.current);
      const analyser = audioCtx.createAnalyser();
      source.connect(analyser);
      const dataArray = new Uint8Array(analyser.fftSize);
      
      const tick = () => {
        analyser.getByteTimeDomainData(dataArray);
        let max = 0;
        for (let i = 0; i < dataArray.length; i++) {
          const v = Math.abs(dataArray[i] - 128) / 128;
          if (v > max) max = v;
        }
        setVolume(max);
        animationFrameId.current = requestAnimationFrame(tick);
      };
      tick();

      if (isConnected && websocket.current?.readyState === WebSocket.OPEN) {
        // Set up media recorder for actual audio transmission
        mediaRecorder.current = new MediaRecorder(mediaStream.current, {
          mimeType: 'audio/webm;codecs=opus'
        });

        let audioChunks = [];
        
        mediaRecorder.current.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunks.push(event.data);
          }
        };

        mediaRecorder.current.onstop = () => {
          const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
          sendAudioToServer(audioBlob);
          audioChunks = [];
        };

        mediaRecorder.current.start(1000); // Record in 1-second chunks
        setPhase('listening');
        setTranscript('Listening... speak clearly into your microphone.');
      } else {
        setPhase('demo_listening');
      }

    } catch (err) {
      console.error('Failed to start voice recording:', err);
      setPhase('error');
      setTranscript(`Microphone access failed: ${err.message}. Please ensure you have granted microphone permissions.`);
    }
  };

  const sendAudioToServer = async (audioBlob) => {
    if (!websocket.current || websocket.current.readyState !== WebSocket.OPEN) {
      console.log('WebSocket not connected, cannot send audio');
      return;
    }

    try {
      const arrayBuffer = await audioBlob.arrayBuffer();
      websocket.current.send(arrayBuffer);
      console.log(`Sent ${arrayBuffer.byteLength} bytes of audio to server`);
    } catch (error) {
      console.error('Failed to send audio:', error);
      setTranscript('Error sending audio to server');
    }
  };

  const stop = () => {
    setPhase('stopping');
    
    if (animationFrameId.current) {
      cancelAnimationFrame(animationFrameId.current);
    }
    
    if (mediaRecorder.current && mediaRecorder.current.state === 'recording') {
      mediaRecorder.current.stop();
    }
    
    if (mediaStream.current) {
      mediaStream.current.getTracks().forEach(track => track.stop());
      mediaStream.current = null;
    }
    
    if (websocket.current) {
      websocket.current.close();
      websocket.current = null;
    }
    
    setPhase('idle');
    setTranscript('');
    setVolume(0);
    setIsConnected(false);
  };

  useEffect(() => () => stop(), []);

  return { 
    start, 
    stop, 
    transcript, 
    phase, 
    volume, 
    isConnected,
    isDemoMode: phase === 'demo_mode' || phase === 'demo_listening'
  };
}
