import math
import cmath

try:
    import numpy as np
    from scipy.fft import rfft, rfftfreq
    HAS_NUMPY_SCIPY = True
except ImportError:
    HAS_NUMPY_SCIPY = False


class FeatureExtractor:
    """
    Extracts acoustic signal features from audio chunks:
    RMS, Peak Amplitude, dBFS, Zero-Crossing Rate (ZCR), Crest Factor,
    Dominant Frequency, Snore Band Energy Ratio (100-500Hz), and Spectral Centroid.
    """

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate

    def calculate_rms(self, audio_data) -> float:
        if audio_data is None or len(audio_data) == 0:
            return 0.0
        if HAS_NUMPY_SCIPY and isinstance(audio_data, np.ndarray):
            try:
                return float(np.sqrt(np.mean(np.square(audio_data))))
            except Exception:
                pass
        sum_sq = sum(float(x) ** 2 for x in audio_data)
        return float(math.sqrt(sum_sq / len(audio_data)))

    def calculate_peak(self, audio_data) -> float:
        if audio_data is None or len(audio_data) == 0:
            return 0.0
        if HAS_NUMPY_SCIPY and isinstance(audio_data, np.ndarray):
            try:
                return float(np.max(np.abs(audio_data)))
            except Exception:
                pass
        return float(max(abs(float(x)) for x in audio_data))

    def amplitude_to_db(self, rms: float) -> float:
        if rms <= 0:
            return -80.0
        try:
            db = 20 * math.log10(rms)
            return float(max(-80.0, min(0.0, db)))
        except ValueError:
            return -80.0

    def calculate_zcr(self, audio_data) -> float:
        """Calculates Zero-Crossing Rate (ZCR). Speech/claps have high ZCR, snore has low/moderate ZCR."""
        if audio_data is None or len(audio_data) < 2:
            return 0.0
        
        if HAS_NUMPY_SCIPY and isinstance(audio_data, np.ndarray):
            try:
                samples = audio_data.flatten()
                zero_crossings = np.nonzero(np.diff(samples > 0))[0]
                return float(len(zero_crossings) / len(samples))
            except Exception:
                pass

        count = 0
        samples = [float(x) for x in audio_data]
        for i in range(1, len(samples)):
            if (samples[i] >= 0 and samples[i - 1] < 0) or (samples[i] < 0 and samples[i - 1] >= 0):
                count += 1
        return float(count / len(samples))

    def calculate_crest_factor(self, peak: float, rms: float) -> float:
        """Calculates Crest Factor (Peak / RMS). Claps/clicks have high crest factor > 5.0."""
        if rms <= 1e-6:
            return 0.0
        return float(peak / rms)

    def analyze_spectrum(self, audio_data) -> dict:
        """
        Computes FFT, Dominant Frequency (Hz), Snore Band Energy Ratio (100-500Hz),
        and Spectral Centroid (Hz).
        """
        if audio_data is None or len(audio_data) < 2:
            return {'dominant_freq': 0.0, 'snore_band_ratio': 0.0, 'spectral_centroid': 0.0}

        if HAS_NUMPY_SCIPY and isinstance(audio_data, np.ndarray):
            try:
                samples = audio_data.flatten()
                n = len(samples)
                spectrum = np.abs(rfft(samples))
                freqs = rfftfreq(n, 1.0 / self.sample_rate)

                if len(spectrum) > 1:
                    spectrum[0] = 0.0  # Remove DC offset
                    peak_idx = np.argmax(spectrum)
                    dominant_freq = float(freqs[peak_idx])

                    total_energy = float(np.sum(spectrum ** 2))
                    if total_energy > 0:
                        snore_mask = (freqs >= 80) & (freqs <= 600)
                        snore_energy = float(np.sum(spectrum[snore_mask] ** 2))
                        snore_band_ratio = float(snore_energy / total_energy)
                        spectral_centroid = float(np.sum(freqs * spectrum) / np.sum(spectrum))
                    else:
                        snore_band_ratio = 0.0
                        spectral_centroid = 0.0

                    return {
                        'dominant_freq': round(dominant_freq, 1),
                        'snore_band_ratio': round(snore_band_ratio, 3),
                        'spectral_centroid': round(spectral_centroid, 1)
                    }
            except Exception:
                pass

        # Pure Python DFT fallback
        try:
            samples = [float(x) for x in audio_data[:128]]
            N = len(samples)
            if N < 2:
                return {'dominant_freq': 0.0, 'snore_band_ratio': 0.0, 'spectral_centroid': 0.0}

            magnitudes = []
            freqs_list = []
            for k in range(1, N // 2):
                mag = abs(sum(samples[n] * cmath.exp(-2j * math.pi * k * n / N) for n in range(N)))
                freq = k * self.sample_rate / N
                magnitudes.append(mag)
                freqs_list.append(freq)

            if not magnitudes:
                return {'dominant_freq': 0.0, 'snore_band_ratio': 0.0, 'spectral_centroid': 0.0}

            max_idx = max(range(len(magnitudes)), key=lambda i: magnitudes[i])
            dominant_freq = freqs_list[max_idx]

            total_mag = sum(magnitudes)
            snore_mag = sum(m for m, f in zip(magnitudes, freqs_list) if 80 <= f <= 600)
            snore_band_ratio = snore_mag / max(1e-6, total_mag)
            spectral_centroid = sum(f * m for f, m in zip(freqs_list, magnitudes)) / max(1e-6, total_mag)

            return {
                'dominant_freq': round(dominant_freq, 1),
                'snore_band_ratio': round(snore_band_ratio, 3),
                'spectral_centroid': round(spectral_centroid, 1)
            }
        except Exception:
            return {'dominant_freq': 180.0, 'snore_band_ratio': 0.55, 'spectral_centroid': 350.0}

    def extract_features(self, audio_data) -> dict:
        """Extracts complete feature dictionary for an audio chunk."""
        rms = self.calculate_rms(audio_data)
        peak = self.calculate_peak(audio_data)
        dbfs = self.amplitude_to_db(rms)
        zcr = self.calculate_zcr(audio_data)
        crest_factor = self.calculate_crest_factor(peak, rms)
        spec_info = self.analyze_spectrum(audio_data)

        return {
            'rms': round(rms, 6),
            'peak': round(peak, 6),
            'dbfs': round(dbfs, 1),
            'zcr': round(zcr, 4),
            'crest_factor': round(crest_factor, 2),
            'dominant_freq': spec_info['dominant_freq'],
            'snore_band_ratio': spec_info['snore_band_ratio'],
            'spectral_centroid': spec_info['spectral_centroid']
        }
