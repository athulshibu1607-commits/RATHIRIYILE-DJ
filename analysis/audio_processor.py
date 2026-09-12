import math

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class AudioProcessor:
    """Handles low-level audio signal processing with pure Python fallbacks if C extensions are restricted."""

    def __init__(self, sample_rate=22050, frame_length=1024, hop_length=512):
        self.sample_rate = sample_rate
        self.frame_length = frame_length
        self.hop_length = hop_length

    def calculate_rms(self, audio_data) -> float:
        """Calculates Root Mean Square (RMS) energy of an audio buffer."""
        if audio_data is None or len(audio_data) == 0:
            return 0.0
        
        if HAS_NUMPY and isinstance(audio_data, np.ndarray):
            try:
                return float(np.sqrt(np.mean(np.square(audio_data))))
            except Exception:
                pass

        # Pure Python fallback
        sum_sq = sum(float(x) ** 2 for x in audio_data)
        return float(math.sqrt(sum_sq / len(audio_data)))

    def calculate_peak_amplitude(self, audio_data) -> float:
        """Calculates maximum peak amplitude of an audio buffer."""
        if audio_data is None or len(audio_data) == 0:
            return 0.0

        if HAS_NUMPY and isinstance(audio_data, np.ndarray):
            try:
                return float(np.max(np.abs(audio_data)))
            except Exception:
                pass

        # Pure Python fallback
        return float(max(abs(float(x)) for x in audio_data))

    def amplitude_to_db(self, amplitude: float, ref: float = 1.0) -> float:
        """Converts linear amplitude to decibels (dB)."""
        if amplitude <= 0:
            return -80.0
        try:
            db = 20 * math.log10(amplitude / ref)
            return float(max(db, -80.0))
        except ValueError:
            return -80.0

    def normalize_audio(self, audio_data):
        """Normalizes audio buffer to peak range [-1.0, 1.0]."""
        peak = self.calculate_peak_amplitude(audio_data)
        if peak == 0:
            return audio_data
        
        if HAS_NUMPY and isinstance(audio_data, np.ndarray):
            try:
                return audio_data / peak
            except Exception:
                pass

        return [float(x) / peak for x in audio_data]
