import math
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analysis.frequency_analyzer import FrequencyAnalyzer
from database.db import init_db, create_session, end_session, get_session


def run_phase4_1_bugfix_tests():
    print("==================================================")
    print("SNORESCAN — PHASE 4.1 FFT VISUALIZATION BUGFIX TEST")
    print("==================================================")

    analyzer = FrequencyAnalyzer(sample_rate=16000)

    # 1. Test Session 18 (Real 14-Event Recording)
    print("\n--- TEST 1: Session 18 Real WAV Audio FFT Spectrum Extraction ---")
    session_18 = get_session(18)
    assert session_18 is not None, "Session 18 should exist in SQLite database"
    
    spectrum_chart = analyzer.compute_session_fft_spectrum(18)
    
    print("Session 18 Spectrum Payload:")
    print(f"  Has FFT: {spectrum_chart.get('has_fft')}")
    print(f"  Title: {spectrum_chart.get('title')}")
    print(f"  Frequency Bins: {len(spectrum_chart.get('frequencies', []))}")
    print(f"  Magnitudes Count: {len(spectrum_chart.get('magnitudes', []))}")
    if spectrum_chart.get('debug_info'):
        dbg = spectrum_chart['debug_info']
        print(f"  Debug Info: session_id={dbg['session_id']}, wav={dbg['wav_path']}, sample_rate={dbg['sample_rate']}, total_samples={dbg['total_samples']}, valid_events={dbg['valid_events']}, fft_bins={dbg['fft_bins']}, frequency_range={dbg['frequency_range']}")

    assert spectrum_chart.get('has_fft') is True, "Session 18 should produce a valid FFT spectrum!"
    assert len(spectrum_chart.get('frequencies', [])) > 0, "Frequency axis points must not be empty!"
    assert len(spectrum_chart.get('magnitudes', [])) > 0, "Magnitude curve points must not be empty!"
    print("[PASSED] TEST 1: Real session 18 WAV audio FFT spectrum successfully computed for 14 events!")

    # 2. Test Zero-Event Silent Session
    print("\n--- TEST 2: Zero-Event Silent Session Handling ---")
    init_db()
    zero_session_id = create_session()
    end_session(zero_session_id, {'duration_seconds': 10.0, 'total_snores': 0, 'funny_verdict': 'No events'})

    zero_spectrum = analyzer.compute_session_fft_spectrum(zero_session_id)
    print(f"Zero-Event Spectrum Output: has_fft = {zero_spectrum.get('has_fft')}, message = '{zero_spectrum.get('message')}'")

    assert zero_spectrum.get('has_fft') is False, "Zero-event session must report has_fft = False!"
    assert "No valid snore events" in zero_spectrum.get('message', ''), "Message should indicate no valid snore events"
    print("[PASSED] TEST 2: Zero-event session correctly returns has_fft = False with clear message!")

    print("\n==================================================")
    print("ALL PHASE 4.1 BUGFIX TESTS PASSED SUCCESSFULLY!")
    print("==================================================")


if __name__ == '__main__':
    run_phase4_1_bugfix_tests()
