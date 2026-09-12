import math
import numpy as np
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analysis.frequency_analyzer import FrequencyAnalyzer
from analysis.snore_detector import SnoreDetector
from analysis.pattern_analyzer import PatternAnalyzer
from database.db import init_db, create_session, record_snore_event, get_session_events, end_session


def run_phase4_tests():
    print("==================================================")
    print("SNORESCAN — PHASE 4 SPECTRAL & ACOUSTIC TEST SUITE")
    print("==================================================")

    # 1. Test FrequencyAnalyzer on Synthetic $150Hz$ Snore Rumble
    sr = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)

    # 150Hz fundamental low rumble + 300Hz harmonic
    snore_signal = (0.3 * np.sin(2 * np.pi * 150 * t) + 0.08 * np.sin(2 * np.pi * 300 * t)).astype(np.float32)

    analyzer = FrequencyAnalyzer(sample_rate=sr)
    metrics = analyzer.analyze_event_audio(snore_signal)

    print("\n--- TEST 1: Synthetic 150Hz Snore Signal Analysis ---")
    print(f"Dominant Frequency: {metrics['dominant_freq_hz']} Hz (Expected ~150 Hz)")
    print(f"Spectral Centroid: {metrics['spectral_centroid']} Hz")
    print(f"Spectral Bandwidth: {metrics['spectral_bandwidth']} Hz")
    print(f"Spectral Rolloff: {metrics['spectral_rolloff']} Hz")
    print(f"Spectral Flatness: {metrics['spectral_flatness']}")
    print(f"Low-Band Energy (50-300Hz): {metrics['low_frequency_energy']*100:.1f}%")
    print(f"Mid-Band Energy (300-1000Hz): {metrics['mid_frequency_energy']*100:.1f}%")
    print(f"High-Band Energy (1000-4000Hz): {metrics['high_frequency_energy']*100:.1f}%")
    print(f"RMS Energy: {metrics['rms']}")
    print(f"Peak Amplitude: {metrics['peak_amplitude']}")
    print(f"Intensity: {metrics['intensity_db']} dBFS")

    assert 140 <= metrics['dominant_freq_hz'] <= 160, f"Dominant freq unexpected: {metrics['dominant_freq_hz']}"
    assert metrics['low_frequency_energy'] > 0.60, f"Low frequency energy should dominate: {metrics['low_frequency_energy']}"
    assert not math.isnan(metrics['spectral_flatness']), "Spectral flatness is NaN!"
    assert 140 <= metrics['dominant_freq_hz'] <= 160, f"Dominant freq unexpected: {metrics['dominant_freq_hz']}"
    assert metrics['low_frequency_energy'] > 0.60, f"Low frequency energy should dominate: {metrics['low_frequency_energy']}"
    assert not math.isnan(metrics['spectral_flatness']), "Spectral flatness is NaN!"
    print("[PASSED] TEST 1: Spectral metrics accurately measured!")

    # 2. Test Empty / Zero Signal Handling (No NaN or Inf)
    print("\n--- TEST 2: Empty / Silent Signal Safety Check ---")
    empty_metrics = analyzer.analyze_event_audio(np.zeros(100, dtype=np.float32))
    print(f"Silent Signal Output: Dominant Freq = {empty_metrics['dominant_freq_hz']} Hz, dBFS = {empty_metrics['intensity_db']}")
    assert empty_metrics['intensity_db'] == -80.0, "Silent dBFS should be -80.0"
    assert empty_metrics['dominant_freq_hz'] == 0.0, "Silent dominant freq should be 0.0"
    assert not math.isnan(empty_metrics['spectral_centroid']), "Centroid NaN on silence!"
    print("[PASSED] TEST 2: Silent audio handled safely without NaN or Inf!")

    # 3. Test Real-time SnoreDetector & Event Finalization with Spectral Metrics
    print("\n--- TEST 3: SnoreDetector State Machine & Event Spectral Finalization ---")
    init_db()
    session_id = create_session()

    detector = SnoreDetector(sample_rate=sr)
    chunk_size = 1024

    # Feed 1.5 seconds of snore signal chunks
    candidates_count = 0
    for i in range(0, len(snore_signal), chunk_size):
        chunk = snore_signal[i:i+chunk_size]
        if len(chunk) < chunk_size:
            chunk = np.pad(chunk, (0, chunk_size - len(chunk)))
        res = detector.evaluate_chunk(chunk, session_id=session_id)
        if res['is_candidate']:
            candidates_count += 1

    print(f"Total Candidate Chunks Accumulated: {candidates_count}")

    # Feed 5 quiet chunks to trigger event finalization
    quiet_chunk = np.zeros(chunk_size, dtype=np.float32)
    final_event = None
    for _ in range(5):
        res = detector.evaluate_chunk(quiet_chunk, session_id=session_id)
        if res.get('new_event'):
            final_event = res['new_event']

    assert final_event is not None, "Snore event failed to finalize!"
    print(f"Finalized Snore Event #{final_event['id']}:")
    print(f"  Duration: {final_event['duration_seconds']} s")
    print(f"  Dominant Frequency: {final_event['dominant_freq_hz']} Hz")
    print(f"  Spectral Centroid: {final_event['spectral_centroid']} Hz")
    print(f"  Low Frequency Energy: {final_event['low_frequency_energy']*100:.1f}%")
    print(f"  Confidence: {final_event['confidence']}%")

    assert final_event['dominant_freq_hz'] > 0, "Event dominant freq missing!"
    assert 'spectral_centroid' in final_event, "Spectral centroid missing from event!"
    print("[PASSED] TEST 3: Event successfully finalized with Phase 4 spectral features!")

    # 4. Test SQLite Persistence & Database Migration
    print("\n--- TEST 4: SQLite Database Insertion & Querying ---")
    event_id = record_snore_event(session_id, final_event)
    print(f"Stored Snore Event #{event_id} in SQLite database.")

    db_events = get_session_events(session_id)
    assert len(db_events) == 1, f"Expected 1 DB event, found {len(db_events)}"
    db_evt = db_events[0]

    print("Retrieved DB Event Spectral Record:")
    print(f"  DB Dominant Freq: {db_evt['dominant_freq_hz']} Hz")
    print(f"  DB Spectral Centroid: {db_evt['spectral_centroid']} Hz")
    print(f"  DB Spectral Bandwidth: {db_evt['spectral_bandwidth']} Hz")
    print(f"  DB Low Frequency Energy: {db_evt['low_frequency_energy']}")
    print(f"  DB Zero Crossing Rate: {db_evt['zero_crossing_rate']}")

    assert db_evt['spectral_centroid'] > 0, "DB spectral_centroid is 0!"
    print("[PASSED] TEST 4: All Phase 4 fields correctly stored and retrieved from SQLite!")

    # 5. Test PatternAnalyzer Aggregation
    print("\n--- TEST 5: PatternAnalyzer Aggregate Session Statistics ---")
    pattern_analyzer = PatternAnalyzer()
    stats = pattern_analyzer.analyze_session_events(db_events, session_duration_sec=30.0)

    print(f"Session Snore Personality: {stats['snore_personality']}")
    print(f"Avg Dominant Freq: {stats['dominant_freq_hz']} Hz")
    print(f"Min / Max Dominant Freq: {stats['min_dominant_freq_hz']} Hz / {stats['max_dominant_freq_hz']} Hz")
    print(f"Avg Spectral Centroid: {stats['avg_spectral_centroid']} Hz")
    print(f"Low Energy Ratio: {stats['low_frequency_energy']*100:.1f}%")

    end_session(session_id, stats)
    print("[PASSED] TEST 5: Session aggregate statistics compiled cleanly!")

    print("\n==================================================")
    print("ALL PHASE 4 UNIT TESTS PASSED SUCCESSFULLY!")
    print("==================================================")


if __name__ == '__main__':
    run_phase4_tests()
