import time
import logging
from datetime import datetime
import numpy as np

from analysis.feature_extractor import FeatureExtractor
from analysis.frequency_analyzer import FrequencyAnalyzer

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')


class SnoreDetector:
    """
    Rule-based signal processing real-time snore event detector.
    Analyzes frame features, enforces frequency/crest factor/ZCR rejection rules,
    manages state machine, and isolates event audio for Phase 4 spectral analysis.
    """

    def __init__(self,
                 sample_rate: int = 16000,
                 min_energy_dbfs: float = -75.0,
                 snore_band_min_ratio: float = 0.10,
                 max_zcr: float = 0.45,
                 max_crest_factor: float = 12.0,
                 max_spectral_centroid: float = 3000.0,
                 min_persistence_chunks: int = 1,
                 max_gap_chunks: int = 5):

        self.sample_rate = sample_rate
        self.min_energy_dbfs = min_energy_dbfs
        self.snore_band_min_ratio = snore_band_min_ratio
        self.max_zcr = max_zcr
        self.max_crest_factor = max_crest_factor
        self.max_spectral_centroid = max_spectral_centroid
        self.min_persistence_chunks = min_persistence_chunks
        self.max_gap_chunks = max_gap_chunks

        self.feature_extractor = FeatureExtractor(sample_rate=sample_rate)
        self.frequency_analyzer = FrequencyAnalyzer(sample_rate=sample_rate)

        # State Machine Variables
        self.state = 'IDLE'  # 'IDLE', 'ACCUMULATING', 'EVENT_ACTIVE'
        self.active_event = None
        self.candidate_chunks = []
        self.gap_count = 0
        self.event_counter = 0
        self.detected_events = []

    def reset(self):
        """Resets detector state for a new session."""
        self.state = 'IDLE'
        self.active_event = None
        self.candidate_chunks = []
        self.gap_count = 0
        self.event_counter = 0
        self.detected_events = []

    def evaluate_chunk(self, audio_data, session_id: int, timestamp: float = None) -> dict:
        """
        Evaluates a single audio chunk and returns live event status and detection metrics.
        """
        timestamp = timestamp or time.time()
        features = self.feature_extractor.extract_features(audio_data)

        # Rule-Based Checks for Snore Candidate
        is_energy_ok = features['dbfs'] >= self.min_energy_dbfs
        is_band_ok = features['snore_band_ratio'] >= self.snore_band_min_ratio
        is_zcr_ok = features['zcr'] <= self.max_zcr
        is_transient_rejected = features['crest_factor'] <= self.max_crest_factor
        is_centroid_ok = features['spectral_centroid'] <= self.max_spectral_centroid

        # Final Chunk Candidate Decision
        is_chunk_snore_candidate = (
            is_energy_ok and
            is_band_ok and
            is_zcr_ok and
            is_transient_rejected and
            is_centroid_ok
        )

        rejection_reason = []
        if not is_energy_ok: rejection_reason.append("Low Energy")
        if not is_band_ok: rejection_reason.append("High Freq / Speech")
        if not is_zcr_ok: rejection_reason.append("High ZCR")
        if not is_transient_rejected: rejection_reason.append("Transient Clap/Click Spikes")
        if not is_centroid_ok: rejection_reason.append("High Spectral Centroid")

        # State Machine Logic for Snore Event Tracking
        newly_created_event = None

        if is_chunk_snore_candidate:
            self.gap_count = 0
            self.candidate_chunks.append({
                'timestamp': timestamp,
                'features': features,
                'audio': audio_data.copy() if hasattr(audio_data, 'copy') else audio_data
            })

            if self.state == 'IDLE':
                self.state = 'ACCUMULATING'

            elif self.state == 'ACCUMULATING':
                if len(self.candidate_chunks) >= self.min_persistence_chunks:
                    # Transition to EVENT_ACTIVE: Create new Possible Snore Event
                    self.state = 'EVENT_ACTIVE'
                    self.event_counter += 1
                    self.active_event = {
                        'id': self.event_counter,
                        'event_number': self.event_counter,
                        'session_id': session_id,
                        'start_timestamp': self.candidate_chunks[0]['timestamp'],
                        'start_time': datetime.fromtimestamp(self.candidate_chunks[0]['timestamp']).strftime('%H:%M:%S'),
                        'end_timestamp': timestamp,
                        'end_time': datetime.fromtimestamp(timestamp).strftime('%H:%M:%S'),
                        'duration_seconds': 0.0,
                        'chunks': list(self.candidate_chunks),
                        'confidence': 0.0
                    }
                    logging.info(f"🔔 [POSSIBLE SNORE DETECTED] Session #{session_id} Event #{self.event_counter} started.")

            elif self.state == 'EVENT_ACTIVE':
                self.active_event['chunks'].append({
                    'timestamp': timestamp,
                    'features': features,
                    'audio': audio_data.copy() if hasattr(audio_data, 'copy') else audio_data
                })
                self.active_event['end_timestamp'] = timestamp
                self.active_event['end_time'] = datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')

        else:
            # Chunk is not a snore candidate
            if self.state == 'ACCUMULATING':
                # False alarm transient; reset candidate pool
                self.state = 'IDLE'
                self.candidate_chunks = []

            elif self.state == 'EVENT_ACTIVE':
                self.gap_count += 1
                if self.gap_count > self.max_gap_chunks:
                    # Conclude and finalize active snore event
                    newly_created_event = self._finalize_active_event()
                    self.state = 'IDLE'
                    self.candidate_chunks = []
                    self.gap_count = 0

        # Construct Current Status Payload
        return {
            'is_candidate': is_chunk_snore_candidate,
            'features': features,
            'state': self.state,
            'rejection_reason': ", ".join(rejection_reason) if rejection_reason else "Snore Candidate",
            'is_snore_active': self.state == 'EVENT_ACTIVE',
            'new_event': newly_created_event,
            'current_event_preview': self._build_event_preview(self.active_event) if self.active_event else None
        }

    def _finalize_active_event(self) -> dict:
        """Finalizes the active snore event metrics, calculates confidence score, and performs FFT analysis."""
        if not self.active_event:
            return None

        event_chunks = self.active_event['chunks']
        start_ts = self.active_event['start_timestamp']
        end_ts = self.active_event['end_timestamp']
        duration = max(0.1, round(end_ts - start_ts, 2))

        db_values = [c['features']['dbfs'] for c in event_chunks]
        rms_values = [c['features']['rms'] for c in event_chunks]
        peak_values = [c['features']['peak'] for c in event_chunks]
        band_ratios = [c['features']['snore_band_ratio'] for c in event_chunks]

        avg_db = float(sum(db_values) / len(db_values))
        avg_rms = float(sum(rms_values) / len(rms_values))
        max_peak = float(max(peak_values))
        avg_band_ratio = float(sum(band_ratios) / len(band_ratios))

        # Concatenate audio chunks for Phase 4 Spectral FFT Analysis
        try:
            audio_list = [c['audio'] for c in event_chunks if c.get('audio') is not None]
            if audio_list:
                event_audio = np.concatenate(audio_list, axis=0)
            else:
                event_audio = np.array([], dtype=np.float32)
        except Exception:
            event_audio = np.array([], dtype=np.float32)

        # Run Phase 4 FFT & Spectral Analysis on concatenated event clip
        spectral_metrics = self.frequency_analyzer.analyze_event_audio(event_audio, self.sample_rate)

        # Rule-Based Confidence Calculation Formula (0 - 100%)
        energy_score = min(100.0, max(0.0, ((avg_db - self.min_energy_dbfs) / 30.0) * 100.0))
        band_score = min(100.0, max(0.0, avg_band_ratio * 100.0))
        duration_score = min(100.0, max(0.0, (duration / 2.0) * 100.0))

        confidence = round(0.35 * band_score + 0.35 * energy_score + 0.30 * duration_score, 1)
        confidence = min(98.0, max(45.0, confidence))

        final_event = {
            'id': self.active_event['id'],
            'event_number': self.active_event.get('event_number', self.active_event['id']),
            'session_id': self.active_event['session_id'],
            'start_timestamp': start_ts,
            'end_timestamp': end_ts,
            'start_time': self.active_event['start_time'],
            'end_time': self.active_event['end_time'],
            'duration_seconds': duration,
            'intensity_db': round(avg_db, 1),
            'peak_amplitude': round(max_peak, 6),
            'rms_energy': round(avg_rms, 6),
            'dominant_freq_hz': spectral_metrics['dominant_freq_hz'],
            'confidence': confidence,
            'detection_method': 'Signal-Processing Rule-Based v1',
            'detection_reason': f"Sustained low-freq energy ({avg_band_ratio*100:.0f}% in 80-600Hz snore band)",
            'spectral_centroid': spectral_metrics['spectral_centroid'],
            'spectral_bandwidth': spectral_metrics['spectral_bandwidth'],
            'spectral_rolloff': spectral_metrics['spectral_rolloff'],
            'spectral_flatness': spectral_metrics['spectral_flatness'],
            'zero_crossing_rate': spectral_metrics['zero_crossing_rate'],
            'low_frequency_energy': spectral_metrics['low_frequency_energy'],
            'mid_frequency_energy': spectral_metrics['mid_frequency_energy'],
            'high_frequency_energy': spectral_metrics['high_frequency_energy'],
            'crest_factor': spectral_metrics['crest_factor'],
            'spectrum_chart': spectral_metrics['spectrum_chart']
        }

        self.detected_events.append(final_event)
        self.active_event = None
        logging.info(
            f"✅ [POSSIBLE SNORE FINALIZED] Event #{final_event['id']} | "
            f"Duration: {duration}s | Loudness: {final_event['intensity_db']} dBFS | "
            f"Freq: {final_event['dominant_freq_hz']} Hz | Confidence: {confidence}%"
        )
        return final_event

    def force_finalize_session(self) -> list:
        """Flushes any open active event when session stops."""
        if self.state == 'EVENT_ACTIVE' and self.active_event:
            self._finalize_active_event()
        self.state = 'IDLE'
        return list(self.detected_events)

    def _build_event_preview(self, event) -> dict:
        """Returns lightweight preview dict for live UI alerts."""
        if not event or not event.get('chunks'):
            return None

        event_chunks = event['chunks']
        start_ts = event['start_timestamp']
        duration = round(time.time() - start_ts, 1)

        db_values = [c['features']['dbfs'] for c in event_chunks]
        freq_values = [c['features']['dominant_freq'] for c in event_chunks]

        return {
            'id': event['id'],
            'duration': duration,
            'intensity_db': round(sum(db_values) / len(db_values), 1),
            'dominant_freq_hz': round(sum(freq_values) / len(freq_values), 1),
            'confidence': 75
        }
