/**
 * SNORESCAN - Client Audio Recorder & Mic Stream Helper
 */

class SnoreRecorder {
    constructor() {
        this.audioContext = null;
        this.mediaStream = null;
        this.processor = null;
        this.sessionId = null;
        this.isRecording = false;
        this.pendingUploads = Promise.resolve();
    }

    async requestMicPermission() {
        try {
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('Microphone access requires HTTPS or localhost.');
            }
            this.mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
            return true;
        } catch (err) {
            console.warn("Microphone permission denied or not available:", err);
            return false;
        }
    }

    startCapture(sessionId) {
        this.sessionId = sessionId;
        this.audioContext = new AudioContext();
        const source = this.audioContext.createMediaStreamSource(this.mediaStream);
        this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);
        this.processor.onaudioprocess = event => {
            if (!this.isRecording) return;
            const input = event.inputBuffer.getChannelData(0);
            const ratio = this.audioContext.sampleRate / 16000;
            const outputLength = Math.max(1, Math.floor(input.length / ratio));
            const samples = new Array(outputLength);
            for (let i = 0; i < outputLength; i++) {
                samples[i] = input[Math.min(input.length - 1, Math.floor(i * ratio))];
            }

            this.pendingUploads = this.pendingUploads
                .then(() => fetch('/api/monitoring/audio', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: this.sessionId, samples })
                }))
                .catch(err => console.warn('Browser audio upload failed:', err));
        };
        source.connect(this.processor);
        const silentOutput = this.audioContext.createGain();
        silentOutput.gain.value = 0;
        this.processor.connect(silentOutput);
        silentOutput.connect(this.audioContext.destination);
        this.isRecording = true;
    }

    async stopMicStream() {
        this.isRecording = false;
        await this.pendingUploads;
        if (this.processor) {
            this.processor.disconnect();
            this.processor = null;
        }
        if (this.audioContext) {
            await this.audioContext.close();
            this.audioContext = null;
        }
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }
        this.sessionId = null;
    }
}

window.snoreRecorder = new SnoreRecorder();
