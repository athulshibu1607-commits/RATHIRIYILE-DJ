import math
import cmath
import logging
import os
from datetime import datetime

try:
    import numpy as np
    from scipy.fft import rfft, rfftfreq
    HAS_NUMPY_SCIPY = True
except ImportError:
    HAS_NUMPY_SCIPY = False

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')


class FrequencyAnalyzer:
    """
    Performs FFT, spectral feature analysis (centroid, bandwidth, rolloff, flatness),
    frequency band energy partitioning, and time-domain signal characterization.
    """

    # Configurable Frequency Regions (Hz)
    LOW_BAND = (50, 300)      # Typical snoring fundamental rumble band
    MID_BAND = (300, 1000)    # Nasal / soft tissue harmonic band
    HIGH_BAND = (1000, 4000)  # High frequency hiss / speech band

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate

    def _sanitize(self, val: float, default: float = 0.0) -> float:
        """Safely sanitizes float output to avoid NaN or Infinity values in DB."""
        if val is None or math.isnan(val) or math.isinf(val):
            return float(default)
        return float(val)

    def analyze_event_audio(self, audio_data, sample_rate: int = None) -> dict:
        """
        Performs full spectral and time-domain feature analysis on an audio clip.
        Returns a complete feature dictionary guaranteed free of NaN/Inf values.
        """
        sr = sample_rate or self.sample_rate

        if audio_data is None or len(audio_data) == 0:
            return self._empty_analysis()

        if HAS_NUMPY_SCIPY and isinstance(audio_data, np.ndarray):
            samples = audio_data.flatten()
        else:
            try:
                samples = np.array(audio_data, dtype=np.float32).flatten() if HAS_NUMPY_SCIPY else [float(x) for x in audio_data]
            except Exception:
                samples = []

        n_samples = len(samples)
        if n_samples < 2:
            return self._empty_analysis()

        # 1. Time-Domain Metrics
        if HAS_NUMPY_SCIPY and isinstance(samples, np.ndarray):
            rms = float(np.sqrt(np.mean(np.square(samples))))
            peak = float(np.max(np.abs(samples)))
            
            # Zero Crossing Rate (ZCR)
            zero_crossings = np.nonzero(np.diff(samples > 0))[0]
            zcr = float(len(zero_crossings) / n_samples)
        else:
            sum_sq = sum(float(x) ** 2 for x in samples)
            rms = float(math.sqrt(sum_sq / n_samples))
            peak = float(max(abs(float(x)) for x in samples))
            
            zcr_count = 0
            for i in range(1, len(samples)):
                if (samples[i] >= 0 and samples[i - 1] < 0) or (samples[i] < 0 and samples[i - 1] >= 0):
                    zcr_count += 1
            zcr = float(zcr_count / n_samples)

        rms = self._sanitize(rms, 0.0)
        peak = self._sanitize(peak, 0.0)
        zcr = self._sanitize(zcr, 0.0)

        # dBFS Loudness
        dbfs = -80.0
        if rms > 1e-7:
            dbfs = 20.0 * math.log10(rms)
        dbfs = float(max(-80.0, min(0.0, dbfs)))

        # Crest Factor
        crest_factor = float(peak / rms) if rms > 1e-6 else 0.0
        crest_factor = self._sanitize(crest_factor, 0.0)

        # 2. Spectral Analysis via FFT
        dominant_freq = 0.0
        dominant_mag = 0.0
        spectral_centroid = 0.0
        spectral_bandwidth = 0.0
        spectral_rolloff = 0.0
        spectral_flatness = 0.0
        low_energy = 0.0
        mid_energy = 0.0
        high_energy = 0.0
        spectrum_chart_data = {'frequencies': [], 'magnitudes': []}

        if HAS_NUMPY_SCIPY and isinstance(samples, np.ndarray):
            try:
                # Compute FFT Real Spectrum
                spectrum = np.abs(rfft(samples))
                freqs = rfftfreq(n_samples, 1.0 / sr)

                if len(spectrum) > 1:
                    spectrum[0] = 0.0  # Remove DC component

                    # Dominant Frequency
                    peak_idx = np.argmax(spectrum)
                    dominant_freq = float(freqs[peak_idx])
                    dominant_mag = float(spectrum[peak_idx])

                    total_energy = float(np.sum(spectrum ** 2))
                    total_mag_sum = float(np.sum(spectrum))

                    if total_mag_sum > 1e-6:
                        # Spectral Centroid
                        spectral_centroid = float(np.sum(freqs * spectrum) / total_mag_sum)

                        # Spectral Bandwidth
                        spectral_bandwidth = float(np.sqrt(np.sum(((freqs - spectral_centroid) ** 2) * spectrum) / total_mag_sum))

                    if total_energy > 1e-9:
                        # Spectral Rolloff (85% of total energy)
                        cum_energy = np.cumsum(spectrum ** 2)
                        rolloff_idx = np.where(cum_energy >= 0.85 * total_energy)[0]
                        if len(rolloff_idx) > 0:
                            spectral_rolloff = float(freqs[rolloff_idx[0]])

                        # Spectral Flatness (Geometric Mean / Arithmetic Mean of Power Spectrum)
                        power_spec = spectrum ** 2 + 1e-12
                        arithmetic_mean = np.mean(power_spec)
                        log_mean = np.mean(np.log(power_spec))
                        geometric_mean = np.exp(log_mean)
                        spectral_flatness = float(geometric_mean / max(1e-12, arithmetic_mean))
                        spectral_flatness = min(1.0, max(0.0, spectral_flatness))

                        # Frequency Band Energies
                        low_mask = (freqs >= self.LOW_BAND[0]) & (freqs <= self.LOW_BAND[1])
                        mid_mask = (freqs >= self.MID_BAND[0]) & (freqs <= self.MID_BAND[1])
                        high_mask = (freqs >= self.HIGH_BAND[0]) & (freqs <= self.HIGH_BAND[1])

                        low_energy = float(np.sum(spectrum[low_mask] ** 2) / total_energy)
                        mid_energy = float(np.sum(spectrum[mid_mask] ** 2) / total_energy)
                        high_energy = float(np.sum(spectrum[high_mask] ** 2) / total_energy)

                    # Downsample spectrum for UI visualization (up to 50 bins)
                    bin_size = max(1, len(freqs) // 50)
                    sampled_freqs = [round(float(f), 1) for f in freqs[::bin_size][:50]]
                    sampled_mags = [round(float(m), 4) for m in spectrum[::bin_size][:50]]
                    spectrum_chart_data = {
                        'frequencies': sampled_freqs,
                        'magnitudes': sampled_mags
                    }
            except Exception as err:
                logging.error(f"[FREQUENCY ANALYZER FFT ERROR] {err}")

        return {
            'rms': round(self._sanitize(rms), 6),
            'peak_amplitude': round(self._sanitize(peak), 6),
            'intensity_db': round(self._sanitize(dbfs, -80.0), 1),
            'crest_factor': round(self._sanitize(crest_factor), 2),
            'zero_crossing_rate': round(self._sanitize(zcr), 4),
            'dominant_freq_hz': round(self._sanitize(dominant_freq), 1),
            'dominant_freq_magnitude': round(self._sanitize(dominant_mag), 4),
            'spectral_centroid': round(self._sanitize(spectral_centroid), 1),
            'spectral_bandwidth': round(self._sanitize(spectral_bandwidth), 1),
            'spectral_rolloff': round(self._sanitize(spectral_rolloff), 1),
            'spectral_flatness': round(self._sanitize(spectral_flatness), 4),
            'low_frequency_energy': round(self._sanitize(low_energy), 4),
            'mid_frequency_energy': round(self._sanitize(mid_energy), 4),
            'high_frequency_energy': round(self._sanitize(high_energy), 4),
            'spectrum_chart': spectrum_chart_data
        }

    def compute_session_fft_spectrum(self, session_id: int) -> dict:
        """
        Loads the actual recorded WAV file for a session, extracts the audio segments
        corresponding to all detected snore events, calculates their FFT magnitude spectra,
        and averages them into a representative FFT spectrum curve for visualization.
        """
        if not HAS_NUMPY_SCIPY:
            return {'has_fft': False, 'frequencies': [], 'magnitudes': [], 'message': 'NumPy / SciPy unavailable.'}

        from database.db import get_session, get_session_events

        session = get_session(session_id)
        if not session:
            logging.info(f"FFT DEBUG: session_id={session_id} not found in database.")
            return {'has_fft': False, 'frequencies': [], 'magnitudes': [], 'message': 'Session record not found'}

        events = get_session_events(session_id)
        if not events or len(events) == 0:
            logging.info(f"FFT DEBUG: session_id={session_id} has 0 valid detected events.")
            return {'has_fft': False, 'frequencies': [], 'magnitudes': [], 'message': 'No valid snore events detected during this session.'}

        audio_rel_path = session.get('audio_file_path', '')
        if not audio_rel_path:
            audio_rel_path = f"recordings/raw/session_{session_id}.wav"

        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        wav_path = os.path.join(project_root, audio_rel_path.replace('/', os.sep))

        if not os.path.exists(wav_path):
            wav_path = os.path.join(project_root, 'recordings', 'raw', f"session_{session_id}.wav")

        if not os.path.exists(wav_path) or os.path.getsize(wav_path) == 0:
            logging.info(f"FFT DEBUG: session_id={session_id} WAV file missing or empty at {wav_path}")
            return {'has_fft': False, 'frequencies': [], 'magnitudes': [], 'message': 'Session audio recording WAV file unavailable.'}

        try:
            import soundfile as sf
            audio_data, sr = sf.read(wav_path)
        except Exception as err:
            logging.error(f"FFT DEBUG ERROR: Failed to open WAV file {wav_path}: {err}")
            return {'has_fft': False, 'frequencies': [], 'magnitudes': [], 'message': 'Failed to parse session WAV audio.'}

        if audio_data is None or len(audio_data) == 0 or sr <= 0:
            logging.info(f"FFT DEBUG: session_id={session_id} audio_data is empty.")
            return {'has_fft': False, 'frequencies': [], 'magnitudes': [], 'message': 'Empty audio data.'}

        if audio_data.ndim > 1:
            audio_data = audio_data.mean(axis=1)

        total_samples = len(audio_data)
        logging.info(f"FFT DEBUG: session_id={session_id}, wav={wav_path}, sample_rate={sr}, total_samples={total_samples}, valid_events={len(events)}")

        # Parse session start time
        sess_start_str = session.get('start_time')
        sess_dt = None
        if sess_start_str:
            try:
                sess_dt = datetime.fromisoformat(sess_start_str)
            except Exception:
                sess_dt = None

        n_grid = 100
        nyquist = sr / 2.0
        grid_freqs = np.linspace(50.0, min(4000.0, nyquist), n_grid)
        event_spectra = []

        for ev in events:
            rel_start = None
            if ev.get('start_timestamp') and session.get('start_timestamp'):
                try:
                    rel_start = max(0.0, float(ev['start_timestamp']) - float(session['start_timestamp']))
                except Exception:
                    rel_start = None
            
            if rel_start is None and sess_dt and ev.get('start_time'):
                try:
                    t_str = str(ev['start_time'])
                    parts = t_str.split(':')
                    if len(parts) >= 3:
                        h, m, s = int(parts[0]), int(parts[1]), int(float(parts[2]))
                        ev_dt = sess_dt.replace(hour=h, minute=m, second=s)
                        rel_start = (ev_dt - sess_dt).total_seconds()
                        if rel_start < 0:
                            rel_start += 86400  # wrap midnight
                except Exception:
                    rel_start = None

            if rel_start is None:
                # Fallback: estimate position from event index ratio
                idx_ratio = (ev.get('id', 1) - 1) / max(1, len(events))
                rel_start = idx_ratio * (total_samples / sr)

            dur = max(0.1, float(ev.get('duration_seconds', 0.5)))
            start_idx = max(0, int(rel_start * sr))
            end_idx = min(total_samples, int((rel_start + dur) * sr))

            clip = audio_data[start_idx:end_idx]
            if len(clip) < 32:
                mid = start_idx if start_idx < total_samples else total_samples // 2
                clip = audio_data[max(0, mid - int(0.25 * sr)):min(total_samples, mid + int(0.25 * sr))]

            if len(clip) < 32:
                continue

            try:
                windowed = clip * np.hanning(len(clip))
                spec = np.abs(rfft(windowed))
                freqs = rfftfreq(len(clip), 1.0 / sr)

                if len(spec) > 1:
                    spec[0] = 0.0  # Remove DC offset
                    interp_spec = np.interp(grid_freqs, freqs, spec)
                    max_val = np.max(interp_spec)
                    if max_val > 1e-6:
                        interp_spec = interp_spec / max_val
                    event_spectra.append(interp_spec)
            except Exception as err:
                logging.error(f"FFT event clip calculation error: {err}")

        if not event_spectra:
            logging.info(f"FFT DEBUG: session_id={session_id} could not compute valid event FFT spectra.")
            return {'has_fft': False, 'frequencies': [], 'magnitudes': [], 'message': 'Unable to calculate FFT for events.'}

        avg_spectrum = np.mean(event_spectra, axis=0)
        logging.info(f"FFT DEBUG: session_id={session_id}, valid_events={len(events)}, fft_bins={len(grid_freqs)}, frequency_range=0-{int(nyquist)} Hz")

        return {
            'has_fft': True,
            'title': f'Average FFT Spectrum of {len(events)} Detected Events',
            'frequencies': [round(float(f), 1) for f in grid_freqs],
            'magnitudes': [round(float(m), 4) for m in avg_spectrum],
            'debug_info': {
                'session_id': session_id,
                'wav_path': wav_path,
                'sample_rate': sr,
                'total_samples': total_samples,
                'valid_events': len(events),
                'fft_bins': len(grid_freqs),
                'frequency_range': f"0-{int(nyquist)} Hz"
            }
        }

    def _empty_analysis(self) -> dict:
        return {
            'rms': 0.0,
            'peak_amplitude': 0.0,
            'intensity_db': -80.0,
            'crest_factor': 0.0,
            'zero_crossing_rate': 0.0,
            'dominant_freq_hz': 0.0,
            'dominant_freq_magnitude': 0.0,
            'spectral_centroid': 0.0,
            'spectral_bandwidth': 0.0,
            'spectral_rolloff': 0.0,
            'spectral_flatness': 0.0,
            'low_frequency_energy': 0.0,
            'mid_frequency_energy': 0.0,
            'high_frequency_energy': 0.0,
            'spectrum_chart': {'frequencies': [], 'magnitudes': []}
        }
