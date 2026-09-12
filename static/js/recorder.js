/**
 * SNORESCAN - Client Audio Recorder & Mic Stream Helper
 */

class SnoreRecorder {
    constructor() {
        self.audioContext = null;
        self.mediaStream = null;
        self.isRecording = false;
    }

    async requestMicPermission() {
        try {
            self.mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
            return true;
        } catch (err) {
            console.warn("Microphone permission denied or not available:", err);
            return false;
        }
    }

    stopMicStream() {
        if (self.mediaStream) {
            self.mediaStream.getTracks().forEach(track => track.stop());
            self.mediaStream = null;
        }
        self.isRecording = false;
    }
}

window.snoreRecorder = new SnoreRecorder();
