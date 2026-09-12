/**
 * SNORESCAN - Client Audio Recorder & Mic Stream Helper
 */

class SnoreRecorder {
    constructor() {
        this.audioContext = null;
        this.mediaStream = null;
        this.sourceNode = null;
        this.processor = null;
        this.sessionId = null;
        this.isRecording = false;
        this.inflightCount = 0;
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
        this.isRecording = true;
        this.inflightCount = 0;

        this.audioContext = new AudioContext();
        this.sourceNode = this.audioContext.createMediaStreamSource(this.mediaStream);
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

            // Fire-and-forget upload (no serialization — prevents backlog)
            this.inflightCount++;
            fetch('/api/monitoring/audio', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: this.sessionId, samples })
            })
            .catch(err => console.warn('Browser audio upload failed:', err))
            .finally(() => { this.inflightCount--; });
        };

        this.sourceNode.connect(this.processor);
        const silentOutput = this.audioContext.createGain();
        silentOutput.gain.value = 0;
        this.processor.connect(silentOutput);
        silentOutput.connect(this.audioContext.destination);
    }

    async stopMicStream() {
        this.isRecording = false;

        // Disconnect processor immediately to stop new audio events
        try {
            if (this.processor) {
                this.processor.onaudioprocess = null;
                this.processor.disconnect();
            }
        } catch (e) { console.warn('Error disconnecting processor:', e); }
        this.processor = null;

        try {
            if (this.sourceNode) this.sourceNode.disconnect();
        } catch (e) { console.warn('Error disconnecting source:', e); }
        this.sourceNode = null;

        // Wait briefly for in-flight uploads to land (max 2 seconds)
        const deadline = Date.now() + 2000;
        while (this.inflightCount > 0 && Date.now() < deadline) {
            await new Promise(r => setTimeout(r, 50));
        }
        if (this.inflightCount > 0) {
            console.warn(`Stopping with ${this.inflightCount} uploads still in-flight (timed out).`);
        }

        // Close audio context
        try {
            if (this.audioContext && this.audioContext.state !== 'closed') {
                await this.audioContext.close();
            }
        } catch (e) { console.warn('Error closing audio context:', e); }
        this.audioContext = null;

        // Stop media stream tracks (turns off mic indicator)
        try {
            if (this.mediaStream) {
                this.mediaStream.getTracks().forEach(track => track.stop());
            }
        } catch (e) { console.warn('Error stopping media stream:', e); }
        this.mediaStream = null;
        this.sessionId = null;
        this.inflightCount = 0;
    }
}

window.snoreRecorder = new SnoreRecorder();
