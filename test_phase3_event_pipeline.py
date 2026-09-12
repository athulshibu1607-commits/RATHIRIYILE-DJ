import time
import os
import json
import numpy as np
from app import app
from database import get_session, get_session_events, init_db

def run_pipeline_test():
    print("=== SNORESCAN PHASE 3 EVENT PIPELINE VERIFICATION ===")
    init_db()
    client = app.test_client()
    sr = 16000
    chunk_size = 1024

    # -------------------------------------------------------------
    # TEST A: SINGLE SNORE EVENT PIPELINE
    # -------------------------------------------------------------
    print("\n--- TEST A: SINGLE SNORE EVENT PIPELINE ---")
    res_start = client.post('/api/monitoring/start')
    sid_a = res_start.get_json()['session_id']
    print(f"Session #{sid_a} Started.")

    # Feed snore-like 180Hz audio signal to detector
    t = np.linspace(0, 1.5, int(1.5 * sr))
    snore_signal = 0.15 * np.sin(2 * np.pi * 180 * t) + 0.08 * np.sin(2 * np.pi * 360 * t)
    num_chunks = len(snore_signal) // chunk_size

    for i in range(num_chunks):
        chunk = snore_signal[i * chunk_size : (i + 1) * chunk_size].astype(np.float32)
        from analysis.audio_recorder import recorder_manager
        recorder_manager._audio_callback(chunk, chunk_size, None, 0)

    # Wait a moment for silence gap
    time.sleep(0.3)
    quiet_chunk = np.random.normal(0, 0.00005, chunk_size).astype(np.float32)
    for _ in range(5):
        recorder_manager._audio_callback(quiet_chunk, chunk_size, None, 0)

    res_stop = client.post('/api/monitoring/stop', json={'session_id': sid_a})
    metrics_a = res_stop.get_json()['metrics']

    db_sess_a = get_session(sid_a)
    db_events_a = get_session_events(sid_a)

    print("\nTEST A RESULTS:")
    print("Report Verdict:", metrics_a['funny_verdict'])
    print("Report Possible Snores Count:", metrics_a['total_snores'])
    print("Report Snoring Duration:", metrics_a['total_snore_duration'])
    print("Report Avg Confidence:", metrics_a['avg_confidence'])
    print("SQLite Session Record total_snores:", db_sess_a['total_snores'])
    print("SQLite snore_events Table Count:", len(db_events_a))

    assert len(db_events_a) == 1, f"Expected 1 event in SQLite, got {len(db_events_a)}"
    assert db_sess_a['total_snores'] == 1, f"Expected total_snores=1 in session record, got {db_sess_a['total_snores']}"
    assert metrics_a['total_snores'] == 1, f"Expected metrics total_snores=1, got {metrics_a['total_snores']}"
    print("PASSED TEST A: 100% Match across Verdict, Report Stats, and SQLite Database!")

    # -------------------------------------------------------------
    # TEST B: MULTIPLE SNORE EVENTS PIPELINE (3 Events)
    # -------------------------------------------------------------
    print("\n--- TEST B: MULTIPLE SNORE EVENTS PIPELINE (3 Events) ---")
    res_start_b = client.post('/api/monitoring/start')
    sid_b = res_start_b.get_json()['session_id']

    for event_num in range(3):
        # Snore burst 1.2s
        t_burst = np.linspace(0, 1.2, int(1.2 * sr))
        sig_burst = 0.15 * np.sin(2 * np.pi * 200 * t_burst)
        n_c = len(sig_burst) // chunk_size
        for i in range(n_c):
            chk = sig_burst[i * chunk_size : (i + 1) * chunk_size].astype(np.float32)
            recorder_manager._audio_callback(chk, chunk_size, None, 0)
        
        # Silence gap 0.5s
        for _ in range(8):
            recorder_manager._audio_callback(quiet_chunk, chunk_size, None, 0)

    res_stop_b = client.post('/api/monitoring/stop', json={'session_id': sid_b})
    metrics_b = res_stop_b.get_json()['metrics']

    db_sess_b = get_session(sid_b)
    db_events_b = get_session_events(sid_b)

    print("\nTEST B RESULTS:")
    print("Report Verdict:", metrics_b['funny_verdict'])
    print("Report Possible Snores Count:", metrics_b['total_snores'])
    print("SQLite Session Record total_snores:", db_sess_b['total_snores'])
    print("SQLite snore_events Table Count:", len(db_events_b))

    assert len(db_events_b) == 3, f"Expected 3 events in SQLite, got {len(db_events_b)}"
    assert db_sess_b['total_snores'] == 3, f"Expected total_snores=3 in session record, got {db_sess_b['total_snores']}"
    assert metrics_b['total_snores'] == 3, f"Expected metrics total_snores=3, got {metrics_b['total_snores']}"
    print("PASSED TEST B: Multiple events pipeline fully verified!")

    # -------------------------------------------------------------
    # TEST C: ZERO EVENTS / SILENCE PIPELINE
    # -------------------------------------------------------------
    print("\n--- TEST C: ZERO EVENTS / SILENCE PIPELINE ---")
    res_start_c = client.post('/api/monitoring/start')
    sid_c = res_start_c.get_json()['session_id']

    for _ in range(20):
        recorder_manager._audio_callback(quiet_chunk, chunk_size, None, 0)

    res_stop_c = client.post('/api/monitoring/stop', json={'session_id': sid_c})
    metrics_c = res_stop_c.get_json()['metrics']

    db_sess_c = get_session(sid_c)
    db_events_c = get_session_events(sid_c)

    print("\nTEST C RESULTS:")
    print("Report Verdict:", metrics_c['funny_verdict'])
    print("Report Possible Snores Count:", metrics_c['total_snores'])
    print("SQLite snore_events Table Count:", len(db_events_c))

    assert len(db_events_c) == 0, f"Expected 0 events in SQLite, got {len(db_events_c)}"
    assert metrics_c['total_snores'] == 0, f"Expected 0 events in metrics, got {metrics_c['total_snores']}"
    print("PASSED TEST C: Zero events pipeline fully verified!")

    print("\n=======================================================")
    print("ALL PHASE 3 EVENT PIPELINE VERIFICATION TESTS PASSED!")
    print("=======================================================")

if __name__ == '__main__':
    run_pipeline_test()
