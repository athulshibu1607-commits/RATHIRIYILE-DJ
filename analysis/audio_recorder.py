import os
import time
import logging
import threading
import math
import numpy as np

try:
    import sounddevice as sd
    import soundfile as sf
    HAS_SOUND_LIBS = True
except Exception as e:
    HAS_SOUND_LIBS = False
    SOUND_LIB_ERR = str(e)

from analysis.snore_detector import SnoreDetector
from database.db import record_snore_event

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')


class AudioRecorderManager:
    """
    Manages continuous laptop microphone audio capture, real-time chunk feature extraction,
    rule-based snore detection state machine, SQLite event persistence, WAV file saving,
    and live status reporting.
    """

    def __init__(self, sample_rate=16000, channels=1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.is_recording = False
        self.active_session_id = None
        self.stream = None

        # Real-time Snore Detector
        self.snore_detector = SnoreDetector()

        # Live Metrics & Diagnostics
        self.mic_connected = False
        self.selected_device_name = "Unknown"
        self.selected_device_index = None
        self.current_rms = 0.0
        self.current_peak = 0.0
        self.current_db = -80.0
        self.session_peak_db = -80.0
        self.chunks_processed = 0
        self.start_timestamp = None
        self.stream_error = None

        # Snore Detection Tracking
        self.detected_events = []
        self.events_timeline = []
        self.latest_event = None
        self.is_snore_active = False

        # Buffers & Lock
        self.recorded_chunks = []
        self.all_intensities_db = []
        self.lock = threading.Lock()
        self.last_log_time = 0.0

        # Inspect available input hardware
        self.inspect_microphone_devices()

    def inspect_microphone_devices(self):
        """Scans available audio input devices and selects default microphone."""
        if not HAS_SOUND_LIBS:
            self.stream_error = f"Audio capture libraries missing/blocked: {SOUND_LIB_ERR}"
            logging.error(f"[MIC INSPECTION] {self.stream_error}")
            return False

        try:
            devices = sd.query_devices()
            default_in = sd.default.device[0]

            logging.info("=== SNORESCAN MICROPHONE DIAGNOSTICS ===")
            logging.info(f"Available Audio Devices: {len(devices)}")

            input_devices = []
            for idx, dev in enumerate(devices):
                if dev['max_input_channels'] > 0:
                    input_devices.append((idx, dev['name'], dev['max_input_channels'], dev['default_samplerate']))

            if not input_devices:
                self.stream_error = "No audio input hardware (microphone) detected."
                logging.error(f"[MIC INSPECTION] {self.stream_error}")
                self.mic_connected = False
                return False

            if default_in is not None and 0 <= default_in < len(devices) and devices[default_in]['max_input_channels'] > 0:
                self.selected_device_index = default_in
                self.selected_device_name = devices[default_in]['name']
            else:
                self.selected_device_index = input_devices[0][0]
                self.selected_device_name = input_devices[0][1]

            self.mic_connected = True
            logging.info(f"Selected Input Device: #{self.selected_device_index} '{self.selected_device_name}'")
            logging.info("=========================================")
            return True

        except Exception as err:
            self.stream_error = f"Failed to query microphone devices: {err}"
            logging.error(f"[MIC INSPECTION ERROR] {self.stream_error}")
            self.mic_connected = False
            return False

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback executed for every incoming microphone audio chunk."""
        if status:
            logging.warning(f"[AUDIO CALLBACK STATUS] {status}")

        if indata is None or len(indata) == 0:
            return

        if indata.ndim > 1 and indata.shape[1] > 1:
            chunk = indata[:, 0].copy().flatten()
        else:
            chunk = indata.copy().flatten()
        now = time.time()

        # Run Snore Detection Evaluation on Chunk
        eval_result = self.snore_detector.evaluate_chunk(chunk, self.active_session_id, now)
        features = eval_result['features']

        rms = features['rms']
        peak = features['peak']
        db = features['dbfs']

        with self.lock:
            self.recorded_chunks.append(chunk)
            self.all_intensities_db.append(db)
            self.current_rms = rms
            self.current_peak = peak
            self.current_db = db
            if db > self.session_peak_db:
                self.session_peak_db = db
            self.chunks_processed += 1
            self.is_snore_active = eval_result['is_snore_active']

            # Handle Newly Finalized Snore Event
            new_event = eval_result.get('new_event')
            if new_event:
                self.detected_events.append(new_event)
                self.latest_event = new_event

                # Format Timeline Entry
                elapsed_sec = int(new_event['start_timestamp'] - (self.start_timestamp or now))
                mins, secs = divmod(elapsed_sec, 60)
                time_str = f"{mins:02d}:{secs:02d}"
                timeline_entry = f"{time_str} — Possible snore ({new_event['duration_seconds']}s, {new_event['confidence']}% confidence)"
                self.events_timeline.append(timeline_entry)

                # Persist Snore Event to SQLite Database immediately
                try:
                    record_snore_event(self.active_session_id, new_event)
                    new_event['saved_to_db'] = True
                    logging.info(f"💾 [SQLITE SAVED] Live Snore Event #{new_event['id']} stored in database.")
                except Exception as err:
                    logging.error(f"Failed to record snore event in SQLite: {err}")

            # Periodic Console Logging (Every 1 second)
            if now - self.last_log_time >= 1.0:
                self.last_log_time = now
                snore_str = " 🔔 [SNORE ACTIVE]" if self.is_snore_active else ""
                logging.info(
                    f"[REAL MIC AUDIO] Chunk #{self.chunks_processed} | "
                    f"Live: {db:.1f} dBFS | Peak dB: {self.session_peak_db:.1f} dBFS | "
                    f"Freq: {features['dominant_freq']:.0f}Hz | Snores: {len(self.detected_events)}{snore_str}"
                )

    def _reset_session_state(self, session_id: int):
        with self.lock:
            self.active_session_id = session_id
            self.recorded_chunks = []
            self.all_intensities_db = []
            self.current_rms = 0.0
            self.current_peak = 0.0
            self.current_db = -80.0
            self.session_peak_db = -80.0
            self.chunks_processed = 0
            self.start_timestamp = time.time()
            self.stream_error = None
            self.snore_detector.reset()
            self.detected_events = []
            self.events_timeline = []
            self.latest_event = None
            self.is_snore_active = False

    def start_recording(self, session_id: int, capture_mode: str = 'server'):
        """Starts continuous microphone audio recording and snore detection."""
        if self.is_recording:
            return True

        if capture_mode == 'browser':
            self._reset_session_state(session_id)
            self.mic_connected = True
            self.selected_device_name = 'Browser microphone'
            self.selected_device_index = None
            self.is_recording = True
            logging.info(f"=== BROWSER MIC RECORDING STARTED FOR SESSION #{session_id} ===")
            return True

        if not self.inspect_microphone_devices():
            return False

        self._reset_session_state(session_id)

        try:
            self.stream = sd.InputStream(
                device=self.selected_device_index,
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='float32',
                callback=self._audio_callback,
                blocksize=1024
            )
            self.stream.start()
            self.is_recording = True
            logging.info(f"=== MIC RECORDING & SNORE DETECTION STARTED FOR SESSION #{session_id} ===")
            return True

        except Exception as err:
            self.stream_error = str(err)
            self.is_recording = False
            logging.error(f"[STREAM ERROR] {err}")
            return False

    def process_browser_chunk(self, audio_data):
        """Processes PCM supplied by the browser microphone capture path."""
        if not self.is_recording:
            return False

        chunk = np.asarray(audio_data, dtype=np.float32).flatten()
        if chunk.size == 0 or chunk.size > self.sample_rate:
            return False

        self._audio_callback(chunk, len(chunk), None, 0)
        return True

    def stop_recording(self, session_id: int):
        """Stops microphone stream, flushes WAV file, finalizes snore events, and computes report metrics."""
        if not self.is_recording:
            return self._empty_session_metrics(0.0)

        logging.info(f"=== STOPPING MIC RECORDING FOR SESSION #{session_id} ===")

        try:
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None
        except Exception as err:
            logging.error(f"Error stopping stream: {err}")

        self.is_recording = False
        elapsed_sec = time.time() - (self.start_timestamp or time.time())

        # Flush any open active snore event in detector
        finalized_events = self.snore_detector.force_finalize_session()
        for ev in finalized_events:
            if not ev.get('saved_to_db'):
                try:
                    record_snore_event(session_id, ev)
                    ev['saved_to_db'] = True
                    logging.info(f"💾 [SQLITE SAVED] Pending Snore Event #{ev['id']} stored in database on session stop.")
                except Exception as err:
                    logging.error(f"Failed to record pending snore event on stop: {err}")

            if ev not in self.detected_events:
                self.detected_events.append(ev)

        with self.lock:
            chunks = list(self.recorded_chunks)
            intensities = list(self.all_intensities_db)
            total_chunks = self.chunks_processed
            peak_db = self.session_peak_db

        if not chunks:
            return self._empty_session_metrics(elapsed_sec)

        try:
            full_audio = np.concatenate(chunks, axis=0)
        except Exception as err:
            logging.error(f"Error concatenating audio: {err}")
            return self._empty_session_metrics(elapsed_sec)

        actual_duration = len(full_audio) / float(self.sample_rate)
        max_peak = float(np.max(np.abs(full_audio)))
        overall_rms = float(np.sqrt(np.mean(np.square(full_audio))))

        # Save to WAV file
        recordings_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'recordings', 'raw')
        os.makedirs(recordings_dir, exist_ok=True)
        wav_filename = f"session_{session_id}.wav"
        wav_path = os.path.join(recordings_dir, wav_filename)
        rel_wav_path = os.path.join('recordings', 'raw', wav_filename).replace('\\', '/')

        try:
            sf.write(wav_path, full_audio, self.sample_rate)
            file_size = os.path.getsize(wav_path) if os.path.exists(wav_path) else 0
        except Exception as err:
            logging.error(f"Error writing WAV file: {err}")
            file_size = 0

        has_non_silent_data = max_peak > 1e-4 and file_size > 0

        valid_intensities = [db for db in intensities if db > -80.0]
        avg_db = float(np.mean(valid_intensities)) if valid_intensities else -80.0
        max_db = peak_db if peak_db > -80.0 else -80.0

        return {
            'duration_seconds': round(actual_duration, 2),
            'total_chunks': total_chunks,
            'avg_intensity_db': round(avg_db, 1) if has_non_silent_data else -80.0,
            'max_intensity_db': round(max_db, 1) if has_non_silent_data else -80.0,
            'avg_rms': round(overall_rms, 6),
            'max_peak': round(max_peak, 6),
            'audio_file_path': rel_wav_path,
            'has_usable_audio': has_non_silent_data
        }

    def _empty_session_metrics(self, duration_sec: float) -> dict:
        return {
            'duration_seconds': round(duration_sec, 2),
            'total_chunks': 0,
            'avg_intensity_db': -80.0,
            'max_intensity_db': -80.0,
            'avg_rms': 0.0,
            'max_peak': 0.0,
            'audio_file_path': '',
            'has_usable_audio': False
        }

    def get_live_status(self) -> dict:
        """Returns real-time status dictionary for live UI monitoring polling API."""
        with self.lock:
            elapsed = time.time() - (self.start_timestamp or time.time()) if self.is_recording else 0.0
            events_list = list(self.detected_events)
            intensities_tail = list(self.all_intensities_db[-50:]) if self.all_intensities_db else []

        snoring_duration = sum(e.get('duration_seconds', 0.0) for e in events_list)
        snoring_percentage = (snoring_duration / max(1.0, elapsed)) * 100.0 if elapsed > 0 else 0.0

        freqs = [e.get('dominant_freq_hz', 0.0) for e in events_list if e.get('dominant_freq_hz', 0.0) > 0]
        event_dbs = [e.get('intensity_db', -80.0) for e in events_list]

        latest_freq = freqs[-1] if freqs else (self.latest_event.get('dominant_freq_hz', 0.0) if self.latest_event else 0.0)
        min_freq = min(freqs) if freqs else 0.0
        max_freq = max(freqs) if freqs else 0.0
        avg_intensity = float(np.mean(event_dbs)) if event_dbs else (self.current_db if self.current_db > -80.0 else -80.0)

        formatted_events = []
        for e in events_list:
            formatted_events.append({
                'id': e.get('id', 1),
                'event_number': e.get('event_number', e.get('id', 1)),
                'start_time': e.get('start_time', ''),
                'end_time': e.get('end_time', ''),
                'duration_seconds': e.get('duration_seconds', 0.0),
                'intensity_db': e.get('intensity_db', -80.0),
                'dominant_freq_hz': e.get('dominant_freq_hz', 0.0),
                'rms_energy': e.get('rms_energy', 0.0),
                'confidence': e.get('confidence', 0.0)
            })

        return {
            'status': 'active' if self.is_recording else 'stopped',
            'monitoring': bool(self.is_recording),
            'session_id': self.active_session_id,
            'mic_connected': self.mic_connected,
            'device_name': self.selected_device_name,
            'device_index': self.selected_device_index,
            'sample_rate': self.sample_rate,
            'channels': self.channels,
            'current_rms': round(self.current_rms, 6),
            'current_peak': round(self.current_peak, 6),
            'current_db': round(self.current_db, 1),
            'session_peak_db': round(self.session_peak_db, 1),
            'chunks_processed': self.chunks_processed,
            'elapsed_seconds': round(elapsed, 1),
            'duration': round(elapsed, 1),
            'stream_error': self.stream_error,
            'possible_snore_count': len(events_list),
            'event_count': len(events_list),
            'snoring_duration': round(snoring_duration, 1),
            'snoring_percentage': round(min(100.0, snoring_percentage), 1),
            'average_intensity': round(avg_intensity, 1),
            'latest_frequency': round(latest_freq, 0),
            'min_frequency': round(min_freq, 0),
            'max_frequency': round(max_freq, 0),
            'is_snore_active': self.is_snore_active,
            'latest_event': self.latest_event,
            'events_timeline': list(self.events_timeline),
            'events': formatted_events,
            'intensity_history': intensities_tail
        }


# Singleton instance export
recorder_manager = AudioRecorderManager()
