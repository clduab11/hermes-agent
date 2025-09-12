/**
 * HERMES Voice Interface Component
 * Real-time voice interaction with legal AI assistant
 */

class VoiceInterface {
    constructor() {
        this.websocket = null;
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioStream = null;
        this.sessionId = null;
        this.audioContext = null;
        this.analyser = null;
        this.microphone = null;
        this.visualizerAnimationId = null;
        
        this.init();
    }

    async init() {
        if (!this.isInitialized) {
            this.createVoiceInterface();
            this.setupEventListeners();
            this.isInitialized = true;
        }
    }

    createVoiceInterface() {
        const container = document.getElementById('voice-interface-container');
        if (!container) return;

        container.innerHTML = `
            <div class="voice-interface">
                <!-- Voice Controls -->
                <div class="voice-controls-section">
                    <div class="voice-control-panel">
                        <div class="voice-status">
                            <div class="connection-indicator">
                                <div class="status-dot offline" id="voice-connection-status"></div>
                                <span class="status-text" id="voice-status-text">Disconnected</span>
                            </div>
                        </div>
                        
                        <div class="voice-visualizer-container">
                            <canvas id="voice-visualizer" width="300" height="150"></canvas>
                            <div class="visualizer-overlay">
                                <button id="voice-record-btn" class="voice-record-button" aria-label="Start voice recording">
                                    <i class="fas fa-microphone"></i>
                                    <span class="pulse-ring"></span>
                                </button>
                            </div>
                        </div>
                        
                        <div class="voice-controls">
                            <button id="start-session-btn" class="control-btn primary">
                                <i class="fas fa-play"></i>
                                Start Session
                            </button>
                            <button id="end-session-btn" class="control-btn secondary" disabled>
                                <i class="fas fa-stop"></i>
                                End Session
                            </button>
                            <button id="mute-btn" class="control-btn secondary">
                                <i class="fas fa-volume-up"></i>
                                Mute
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Conversation Display -->
                <div class="conversation-section">
                    <div class="conversation-header">
                        <h3>
                            <i class="fas fa-comments"></i>
                            Live Conversation
                        </h3>
                        <div class="conversation-controls">
                            <button id="clear-conversation" class="control-btn small">
                                <i class="fas fa-trash"></i>
                                Clear
                            </button>
                            <button id="export-conversation" class="control-btn small">
                                <i class="fas fa-download"></i>
                                Export
                            </button>
                        </div>
                    </div>
                    
                    <div class="conversation-display" id="conversation-display">
                        <div class="welcome-message">
                            <div class="welcome-content">
                                <i class="fas fa-microphone-alt legal-icon"></i>
                                <h4>Welcome to HERMES Legal AI</h4>
                                <p>Start a voice session to begin interacting with your AI legal assistant.</p>
                                <p class="disclaimer">
                                    <i class="fas fa-info-circle"></i>
                                    This system provides general information only and does not constitute legal advice.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Session Metrics -->
                <div class="session-metrics-section">
                    <div class="metrics-header">
                        <h3>Session Metrics</h3>
                    </div>
                    <div class="metrics-grid">
                        <div class="metric-item">
                            <span class="metric-label">Duration</span>
                            <span class="metric-value" id="session-duration">00:00</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">Interactions</span>
                            <span class="metric-value" id="interaction-count">0</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">Avg Response</span>
                            <span class="metric-value" id="avg-response-time">0ms</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">Confidence</span>
                            <span class="metric-value" id="confidence-score">-</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Voice Interface Styles -->
            <style>
                .voice-interface {
                    display: grid;
                    grid-template-columns: 1fr 2fr 1fr;
                    gap: 2rem;
                    height: calc(100vh - 200px);
                }

                /* Voice Controls */
                .voice-control-panel {
                    background: white;
                    border-radius: 12px;
                    padding: 2rem;
                    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 2rem;
                }

                .voice-status {
                    width: 100%;
                    text-align: center;
                }

                .connection-indicator {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 0.5rem;
                }

                .status-dot {
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    background: #e53e3e;
                    animation: pulse 2s infinite;
                }

                .status-dot.online {
                    background: #38a169;
                }

                .status-dot.recording {
                    background: #d69e2e;
                    animation: pulse 0.5s infinite;
                }

                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.5; }
                }

                .voice-visualizer-container {
                    position: relative;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }

                #voice-visualizer {
                    border-radius: 8px;
                    background: #f7fafc;
                    border: 2px solid #e2e8f0;
                }

                .visualizer-overlay {
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                }

                .voice-record-button {
                    width: 80px;
                    height: 80px;
                    border-radius: 50%;
                    border: none;
                    background: linear-gradient(135deg, #1a365d, #2d5a87);
                    color: white;
                    font-size: 2rem;
                    cursor: pointer;
                    position: relative;
                    transition: all 0.3s ease;
                    box-shadow: 0 4px 15px rgba(26, 54, 93, 0.3);
                }

                .voice-record-button:hover {
                    transform: scale(1.05);
                    box-shadow: 0 6px 20px rgba(26, 54, 93, 0.4);
                }

                .voice-record-button.recording {
                    background: linear-gradient(135deg, #e53e3e, #c53030);
                    animation: recordPulse 1s infinite;
                }

                @keyframes recordPulse {
                    0%, 100% { transform: scale(1); }
                    50% { transform: scale(1.1); }
                }

                .pulse-ring {
                    position: absolute;
                    top: -10px;
                    left: -10px;
                    right: -10px;
                    bottom: -10px;
                    border: 3px solid #d69e2e;
                    border-radius: 50%;
                    opacity: 0;
                    animation: pulseRing 2s infinite;
                }

                @keyframes pulseRing {
                    0% {
                        opacity: 0;
                        transform: scale(0.8);
                    }
                    50% {
                        opacity: 0.8;
                    }
                    100% {
                        opacity: 0;
                        transform: scale(1.4);
                    }
                }

                .voice-controls {
                    display: flex;
                    gap: 1rem;
                    flex-wrap: wrap;
                    justify-content: center;
                }

                /* Conversation Display */
                .conversation-section {
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
                    display: flex;
                    flex-direction: column;
                    overflow: hidden;
                }

                .conversation-header {
                    padding: 1.5rem 2rem;
                    border-bottom: 1px solid #e2e8f0;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    background: #f7fafc;
                }

                .conversation-header h3 {
                    color: #1a365d;
                    font-family: 'Crimson Text', serif;
                    font-size: 1.5rem;
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                }

                .conversation-controls {
                    display: flex;
                    gap: 0.5rem;
                }

                .conversation-display {
                    flex: 1;
                    padding: 2rem;
                    overflow-y: auto;
                    max-height: 500px;
                }

                .welcome-message {
                    text-align: center;
                    color: #4a5568;
                    height: 100%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }

                .welcome-content .legal-icon {
                    font-size: 3rem;
                    color: #d69e2e;
                    margin-bottom: 1rem;
                }

                .disclaimer {
                    font-size: 0.875rem;
                    color: #718096;
                    margin-top: 1rem;
                    padding: 1rem;
                    background: #f7fafc;
                    border-radius: 8px;
                    border-left: 4px solid #d69e2e;
                }

                .message {
                    margin-bottom: 1.5rem;
                    padding: 1rem;
                    border-radius: 12px;
                    max-width: 80%;
                    animation: fadeInUp 0.3s ease-out;
                }

                .message.user {
                    background: #ebf8ff;
                    border: 1px solid #bee3f8;
                    margin-left: auto;
                    text-align: right;
                }

                .message.assistant {
                    background: #f0fff4;
                    border: 1px solid #c6f6d5;
                    margin-right: auto;
                }

                .message-header {
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    margin-bottom: 0.5rem;
                    font-size: 0.875rem;
                    color: #4a5568;
                }

                .message-content {
                    color: #2d3748;
                    line-height: 1.6;
                }

                /* Session Metrics */
                .session-metrics-section {
                    background: white;
                    border-radius: 12px;
                    padding: 2rem;
                    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
                }

                .metrics-header h3 {
                    color: #1a365d;
                    font-family: 'Crimson Text', serif;
                    font-size: 1.5rem;
                    margin-bottom: 2rem;
                    text-align: center;
                }

                .metrics-grid {
                    display: flex;
                    flex-direction: column;
                    gap: 1.5rem;
                }

                .metric-item {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    text-align: center;
                    padding: 1rem;
                    border-radius: 8px;
                    background: #f7fafc;
                    border-left: 4px solid #d69e2e;
                }

                .metric-label {
                    font-size: 0.875rem;
                    color: #4a5568;
                    font-weight: 600;
                    margin-bottom: 0.5rem;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }

                .metric-value {
                    font-size: 1.5rem;
                    font-weight: 700;
                    color: #1a365d;
                }

                /* Control Buttons */
                .control-btn {
                    padding: 0.75rem 1.5rem;
                    border: none;
                    border-radius: 8px;
                    font-weight: 600;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    transition: all 0.3s ease;
                    font-size: 0.875rem;
                }

                .control-btn.primary {
                    background: linear-gradient(135deg, #1a365d, #2d5a87);
                    color: white;
                }

                .control-btn.secondary {
                    background: #e2e8f0;
                    color: #4a5568;
                }

                .control-btn.small {
                    padding: 0.5rem 1rem;
                    font-size: 0.8rem;
                }

                .control-btn:hover:not(:disabled) {
                    transform: translateY(-1px);
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                }

                .control-btn:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }

                /* Animations */
                @keyframes fadeInUp {
                    from {
                        opacity: 0;
                        transform: translateY(20px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }

                /* Responsive */
                @media (max-width: 1200px) {
                    .voice-interface {
                        grid-template-columns: 1fr;
                        grid-template-rows: auto 1fr auto;
                    }
                }

                @media (max-width: 768px) {
                    .voice-interface {
                        gap: 1rem;
                    }
                    
                    .voice-control-panel,
                    .session-metrics-section {
                        padding: 1rem;
                    }
                    
                    .conversation-display {
                        padding: 1rem;
                    }
                }
            </style>
        `;
    }

    setupEventListeners() {
        // Voice control buttons
        document.getElementById('start-session-btn')?.addEventListener('click', () => this.startSession());
        document.getElementById('end-session-btn')?.addEventListener('click', () => this.endSession());
        document.getElementById('voice-record-btn')?.addEventListener('click', () => this.toggleRecording());
        document.getElementById('mute-btn')?.addEventListener('click', () => this.toggleMute());
        
        // Conversation controls
        document.getElementById('clear-conversation')?.addEventListener('click', () => this.clearConversation());
        document.getElementById('export-conversation')?.addEventListener('click', () => this.exportConversation());
    }

    async startSession() {
        try {
            // Request microphone permission
            this.audioStream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 16000
                }
            });

            // Setup audio context and analyzer for visualization
            this.setupAudioVisualization();

            // Connect to WebSocket
            await this.connectWebSocket();

            // Update UI
            this.updateConnectionStatus('online', 'Connected');
            document.getElementById('start-session-btn').disabled = true;
            document.getElementById('end-session-btn').disabled = false;

            this.sessionStartTime = Date.now();
            this.startSessionTimer();

        } catch (error) {
            console.error('Failed to start voice session:', error);
            this.showError('Failed to start voice session. Please check your microphone permissions.');
        }
    }

    async connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/voice`;
        
        this.websocket = new WebSocket(wsUrl);
        
        return new Promise((resolve, reject) => {
            this.websocket.onopen = () => {
                console.log('Voice WebSocket connected');
                resolve();
            };
            
            this.websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleVoiceMessage(data);
            };
            
            this.websocket.onclose = () => {
                console.log('Voice WebSocket disconnected');
                this.updateConnectionStatus('offline', 'Disconnected');
            };
            
            this.websocket.onerror = (error) => {
                console.error('Voice WebSocket error:', error);
                reject(error);
            };
        });
    }

    setupAudioVisualization() {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        this.analyser = this.audioContext.createAnalyser();
        this.microphone = this.audioContext.createMediaStreamSource(this.audioStream);
        
        this.analyser.fftSize = 256;
        this.microphone.connect(this.analyser);
        
        this.startVisualization();
    }

    startVisualization() {
        const canvas = document.getElementById('voice-visualizer');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        const bufferLength = this.analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        
        const draw = () => {
            this.visualizerAnimationId = requestAnimationFrame(draw);
            
            this.analyser.getByteFrequencyData(dataArray);
            
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            const barWidth = (canvas.width / bufferLength) * 2.5;
            let x = 0;
            
            for (let i = 0; i < bufferLength; i++) {
                const barHeight = (dataArray[i] / 255) * canvas.height;
                
                const red = (i * 255) / bufferLength;
                const green = 50;
                const blue = 255 - red;
                
                ctx.fillStyle = `rgb(${red}, ${green}, ${blue})`;
                ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
                
                x += barWidth + 1;
            }
        };
        
        draw();
    }

    toggleRecording() {
        if (this.isRecording) {
            this.stopRecording();
        } else {
            this.startRecording();
        }
    }

    async startRecording() {
        if (!this.audioStream) {
            this.showError('Please start a session first');
            return;
        }

        try {
            this.mediaRecorder = new MediaRecorder(this.audioStream);
            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };

            this.mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
                await this.sendAudioData(audioBlob);
            };

            this.mediaRecorder.start();
            this.isRecording = true;
            
            this.updateRecordingUI(true);
            this.updateConnectionStatus('recording', 'Recording...');

        } catch (error) {
            console.error('Failed to start recording:', error);
            this.showError('Failed to start recording');
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.updateRecordingUI(false);
            this.updateConnectionStatus('online', 'Processing...');
        }
    }

    async sendAudioData(audioBlob) {
        if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
            this.showError('WebSocket not connected');
            return;
        }

        // Convert blob to base64 for transmission
        const reader = new FileReader();
        reader.onload = () => {
            const audioData = reader.result.split(',')[1]; // Remove data URL prefix
            
            const message = {
                type: 'audio_data',
                session_id: this.sessionId,
                audio_data: audioData,
                timestamp: Date.now()
            };
            
            this.websocket.send(JSON.stringify(message));
        };
        
        reader.readAsDataURL(audioBlob);
    }

    handleVoiceMessage(data) {
        switch (data.type) {
            case 'transcription':
                this.addMessage('user', data.text, data.timestamp);
                break;
            case 'ai_response':
                this.addMessage('assistant', data.text, data.timestamp);
                if (data.audio_url) {
                    this.playAudioResponse(data.audio_url);
                }
                break;
            case 'session_started':
                this.sessionId = data.session_id;
                break;
            case 'error':
                this.showError(data.message);
                break;
            case 'metrics':
                this.updateSessionMetrics(data.metrics);
                break;
        }
    }

    addMessage(sender, text, timestamp) {
        const conversationDisplay = document.getElementById('conversation-display');
        if (!conversationDisplay) return;

        // Remove welcome message if it exists
        const welcomeMessage = conversationDisplay.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }

        const messageElement = document.createElement('div');
        messageElement.className = `message ${sender}`;
        
        messageElement.innerHTML = `
            <div class="message-header">
                <i class="fas fa-${sender === 'user' ? 'user' : 'robot'}"></i>
                <span>${sender === 'user' ? 'You' : 'HERMES AI'}</span>
                <span class="timestamp">${new Date(timestamp).toLocaleTimeString()}</span>
            </div>
            <div class="message-content">${text}</div>
        `;

        conversationDisplay.appendChild(messageElement);
        conversationDisplay.scrollTop = conversationDisplay.scrollHeight;

        // Update interaction count
        const countElement = document.getElementById('interaction-count');
        if (countElement) {
            const current = parseInt(countElement.textContent) || 0;
            countElement.textContent = current + 1;
        }
    }

    async playAudioResponse(audioUrl) {
        try {
            const audio = new Audio(audioUrl);
            audio.play();
        } catch (error) {
            console.error('Failed to play audio response:', error);
        }
    }

    updateRecordingUI(recording) {
        const recordBtn = document.getElementById('voice-record-btn');
        if (recordBtn) {
            if (recording) {
                recordBtn.classList.add('recording');
                recordBtn.innerHTML = '<i class="fas fa-stop"></i><span class="pulse-ring"></span>';
            } else {
                recordBtn.classList.remove('recording');
                recordBtn.innerHTML = '<i class="fas fa-microphone"></i><span class="pulse-ring"></span>';
            }
        }
    }

    updateConnectionStatus(status, text) {
        const statusDot = document.getElementById('voice-connection-status');
        const statusText = document.getElementById('voice-status-text');
        
        if (statusDot) {
            statusDot.className = `status-dot ${status}`;
        }
        
        if (statusText) {
            statusText.textContent = text;
        }
    }

    startSessionTimer() {
        this.sessionTimer = setInterval(() => {
            const elapsed = Date.now() - this.sessionStartTime;
            const minutes = Math.floor(elapsed / 60000);
            const seconds = Math.floor((elapsed % 60000) / 1000);
            
            const durationElement = document.getElementById('session-duration');
            if (durationElement) {
                durationElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }
        }, 1000);
    }

    updateSessionMetrics(metrics) {
        const elements = {
            'avg-response-time': `${metrics.avgResponseTime || 0}ms`,
            'confidence-score': `${Math.round((metrics.confidenceScore || 0) * 100)}%`
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
    }

    endSession() {
        // Stop recording if active
        if (this.isRecording) {
            this.stopRecording();
        }

        // Stop audio stream
        if (this.audioStream) {
            this.audioStream.getTracks().forEach(track => track.stop());
            this.audioStream = null;
        }

        // Stop visualization
        if (this.visualizerAnimationId) {
            cancelAnimationFrame(this.visualizerAnimationId);
        }

        // Close audio context
        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }

        // Close WebSocket
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }

        // Stop session timer
        if (this.sessionTimer) {
            clearInterval(this.sessionTimer);
        }

        // Update UI
        this.updateConnectionStatus('offline', 'Disconnected');
        document.getElementById('start-session-btn').disabled = false;
        document.getElementById('end-session-btn').disabled = true;
        
        this.showSuccess('Voice session ended');
    }

    toggleMute() {
        // Implementation for muting audio output
        this.showInfo('Mute functionality coming soon');
    }

    clearConversation() {
        const conversationDisplay = document.getElementById('conversation-display');
        if (conversationDisplay) {
            conversationDisplay.innerHTML = `
                <div class="welcome-message">
                    <div class="welcome-content">
                        <i class="fas fa-microphone-alt legal-icon"></i>
                        <h4>Conversation Cleared</h4>
                        <p>Start a new voice session to begin interacting with your AI legal assistant.</p>
                    </div>
                </div>
            `;
        }

        // Reset interaction count
        const countElement = document.getElementById('interaction-count');
        if (countElement) {
            countElement.textContent = '0';
        }
    }

    exportConversation() {
        const messages = document.querySelectorAll('.message');
        if (messages.length === 0) {
            this.showInfo('No conversation to export');
            return;
        }

        let exportText = `HERMES Legal AI Conversation Export\nDate: ${new Date().toLocaleString()}\n\n`;
        
        messages.forEach(message => {
            const header = message.querySelector('.message-header span').textContent;
            const content = message.querySelector('.message-content').textContent;
            const timestamp = message.querySelector('.timestamp').textContent;
            
            exportText += `[${timestamp}] ${header}:\n${content}\n\n`;
        });

        const blob = new Blob([exportText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `hermes-conversation-${Date.now()}.txt`;
        a.click();
        
        URL.revokeObjectURL(url);
        this.showSuccess('Conversation exported successfully');
    }

    // Utility methods
    showError(message) {
        if (window.HermesApp) {
            window.HermesApp.showToast(message, 'error');
        }
    }

    showSuccess(message) {
        if (window.HermesApp) {
            window.HermesApp.showToast(message, 'success');
        }
    }

    showInfo(message) {
        if (window.HermesApp) {
            window.HermesApp.showToast(message, 'info');
        }
    }
}

// Initialize when script loads
window.VoiceInterface = new VoiceInterface();