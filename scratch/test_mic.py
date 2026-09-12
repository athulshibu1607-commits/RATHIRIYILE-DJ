import time
import os
import sys
import logging
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from analysis.audio_recorder import AudioRecorderManager
from analysis.snore_detector import SnoreDetector
from database.db import create_session

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')

def test_detector_synthetic():
    print("\n--- SYNTHETIC SNORE DETECTOR TEST ---")
    detector = SnoreDetector()
    detector.reset()

    # Generate 150 Hz snore-like acoustic signal (duration 1 second = 16000 samples)
    t = np.linspace(0, 1.0, 16000, endpoint=False)
    # Fundamental 150Hz + harmonics 300Hz + noise
    snore_audio = 0.05 * np.sin(2 * np.pi * 150 * t) + 0.02 * np.sin(2 * np.pi * 300 * t) + 0.005 * np.random.randn(16000)

    # Process in 1024-sample blocks
    block_size = 1024
    num_blocks = len(snore_audio) // block_size
    events_found = []

    print(f"Processing {num_blocks} audio blocks of synthetic 150Hz snore sound...")
    for i in range(num_blocks):
        block = snore_audio[i*block_size:(i+1)*block_size]
        res = detector.evaluate_chunk(block, session_id=999)
        if res.get('new_event'):
            events_found.append(res['new_event'])
            print(f"🔔 Event Detected at Block {i}: {res['new_event']}")

    # Finalize remaining active event if any
    finalized = detector.force_finalize_session()
    for ev in finalized:
        if ev not in events_found:
            events_found.append(ev)

    print(f"Total Detected Events: {len(events_found)}")
    assert len(events_found) > 0, "Synthetic snore test failed! Detector should identify 150Hz snore signal."
    print("--- SYNTHETIC TEST PASSED SUCCESSFULLY ---\n")

def test_mic():
    print("--- HARDWARE MICROPHONE DIAGNOSTIC ---")
    recorder = AudioRecorderManager()
    print(f"Mic Connected: {recorder.mic_connected}")
    print(f"Device Name: {recorder.selected_device_name}")

    sess_id = create_session()
    started = recorder.start_recording(sess_id)
    print(f"Recording Started: {started}")

    if started:
        time.sleep(3)
        status = recorder.get_live_status()
        print(f"Live Metrics after 3s: RMS={status['current_rms']:.6f}, dBFS={status['current_db']:.1f}, Chunks={status['chunks_processed']}")
        metrics = recorder.stop_recording(sess_id)
        print(f"Final Metrics: Chunks={metrics.get('total_chunks')}, Snores={metrics.get('total_snores')}")
    print("--- HARDWARE MIC DIAGNOSTIC COMPLETE ---\n")

if __name__ == '__main__':
    test_detector_synthetic()
    test_mic()
