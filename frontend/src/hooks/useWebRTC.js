import { useEffect, useRef, useState } from 'react';

export default function useWebRTC() {
  const mediaStream = useRef(null);
  const animationFrameId = useRef(null);
  const [transcript, setTranscript] = useState('');
  const [phase, setPhase] = useState('idle');
  const [volume, setVolume] = useState(0);

  const start = async () => {
    try {
      setPhase('listening');
      mediaStream.current = await navigator.mediaDevices.getUserMedia({ audio: true });
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
      // placeholder transcript
      setTranscript('Listening...');
    } catch (err) {
      console.error('Failed to get user media:', err);
      setPhase('idle');
    }
  };

  const stop = () => {
    if (animationFrameId.current) {
      cancelAnimationFrame(animationFrameId.current);
    }
    mediaStream.current?.getTracks().forEach(t => t.stop());
    setPhase('idle');
    setTranscript('');
  };

  useEffect(() => () => stop(), []);

  return { start, stop, transcript, phase, volume };
}
