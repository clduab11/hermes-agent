import { useEffect, useRef, useState } from 'react';

export default function useWebRTC() {
  const mediaStream = useRef(null);
  const [transcript, setTranscript] = useState('');
  const [phase, setPhase] = useState('idle');
  const [volume, setVolume] = useState(0);

  const start = async () => {
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
      requestAnimationFrame(tick);
    };
    tick();
    // placeholder transcript
    setTranscript('Listening...');
  };

  const stop = () => {
    mediaStream.current?.getTracks().forEach(t => t.stop());
    setPhase('idle');
    setTranscript('');
  };

  return { start, stop, transcript, phase, volume };
}
