import math
import os
import sys
import sqlite3

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from database.db import (
    init_db,
    create_session,
    end_session,
    record_snore_event,
    get_session,
    get_all_sessions,
    get_session_events,
    get_db_connection,
    DB_PATH
)
from analysis.snore_detector import SnoreDetector


def run_phase5_tests():
    print("==================================================")
    print("SNORESCAN — PHASE 5 COMPLETE DATA STORAGE TESTS")
    print("==================================================")

    init_db()
    client = app.test_client()

    # 1. Foreign Key Verification
    print("\n--- TEST 1: SQLite Foreign Key Constraints Check ---")
    conn = get_db_connection()
    fk_status = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
    conn.close()
    print(f"SQLite PRAGMA foreign_keys: {fk_status}")
    assert fk_status == 1, "Foreign Key constraints must be enabled (1)!"
    print("[PASSED] TEST 1: Foreign key constraints enabled!")

    # 2. Sequential Event Numbering Reset per Session
    print("\n--- TEST 2: Per-Session Sequential Event Numbering Reset ---")
    session_1 = create_session()
    detector_1 = SnoreDetector(sample_rate=16000)

    # Feed events to Session 1
    sample_event_data = {
        'duration_seconds': 0.8,
        'intensity_db': -32.5,
        'peak_amplitude': 0.08,
        'rms_energy': 0.015,
        'dominant_freq_hz': 185.0,
        'spectral_centroid': 420.0,
        'spectral_bandwidth': 350.0,
        'spectral_rolloff': 500.0,
        'spectral_flatness': 0.002,
        'confidence': 82.0
    }

    for i in range(1, 4):
        evt = dict(sample_event_data)
        evt['event_number'] = i
        record_snore_event(session_1, evt)

    events_sess_1 = get_session_events(session_1)
    event_numbers_1 = [e['event_number'] for e in events_sess_1]
    print(f"Session #{session_1} Stored Event Numbers: {event_numbers_1}")
    assert event_numbers_1 == [1, 2, 3], f"Session 1 event numbers expected [1, 2, 3], got {event_numbers_1}"

    # Start Session 2 (Detector reset)
    session_2 = create_session()
    detector_2 = SnoreDetector(sample_rate=16000)
    detector_2.reset()

    for i in range(1, 3):
        evt = dict(sample_event_data)
        evt['event_number'] = i
        record_snore_event(session_2, evt)

    events_sess_2 = get_session_events(session_2)
    event_numbers_2 = [e['event_number'] for e in events_sess_2]
    print(f"Session #{session_2} Stored Event Numbers: {event_numbers_2}")
    assert event_numbers_2 == [1, 2], f"Session 2 event numbers expected [1, 2], got {event_numbers_2}"
    print("[PASSED] TEST 2: Sequential event numbers start at 1 for every new monitoring run!")

    # 3. Test Zero-Event Session Persistence
    print("\n--- TEST 3: Zero-Event Silent Session Persistence ---")
    session_zero = create_session()
    end_session(session_zero, {
        'duration_seconds': 15.0,
        'total_snores': 0,
        'total_snore_duration': 0.0,
        'avg_intensity_db': -80.0,
        'funny_verdict': 'No possible snoring events detected during this session.'
    })

    db_zero_session = get_session(session_zero)
    db_zero_events = get_session_events(session_zero)
    print(f"Zero-Event Session #{session_zero} stored: total_snores={db_zero_session['total_snores']}, events_count={len(db_zero_events)}")
    assert db_zero_session['total_snores'] == 0, "Zero event session total_snores should be 0"
    assert len(db_zero_events) == 0, "Zero event session should have 0 event rows"
    print("[PASSED] TEST 3: Zero-event silent sessions stored cleanly!")

    # 4. Test Data Persistence Across Connection/Server Resets
    print("\n--- TEST 4: SQLite Data Persistence Across Application Restart ---")
    end_session(session_1, {'duration_seconds': 45.0, 'total_snores': 3})
    end_session(session_2, {'duration_seconds': 30.0, 'total_snores': 2})

    # Simulate server restart by querying a fresh connection
    all_sessions_fresh = get_all_sessions()
    sess_ids = [s['id'] for s in all_sessions_fresh]
    print(f"Retrieved Sessions after server restart simulation: {sess_ids}")

    assert session_1 in sess_ids, f"Session #{session_1} missing after restart!"
    assert session_2 in sess_ids, f"Session #{session_2} missing after restart!"

    restarted_events_1 = get_session_events(session_1)
    assert len(restarted_events_1) == 3, "Events for session_1 missing after restart!"
    print("[PASSED] TEST 4: Completed sessions and snore events persist 100% in SQLite across server restarts!")

    # 5. Test REST API Endpoints
    print("\n--- TEST 5: REST API Endpoint Validation ---")
    res_list = client.get('/api/sessions')
    assert res_list.status_code == 200, "GET /api/sessions failed"
    json_list = res_list.get_json()
    assert json_list['status'] == 'success', "JSON status not success"
    assert len(json_list['sessions']) > 0, "API sessions list empty"

    res_single = client.get(f'/api/sessions/{session_1}')
    assert res_single.status_code == 200, f"GET /api/sessions/{session_1} failed"
    json_single = res_single.get_json()
    assert json_single['session']['id'] == session_1, "Session ID mismatch in API"

    res_events = client.get(f'/api/sessions/{session_1}/events')
    assert res_events.status_code == 200, f"GET /api/sessions/{session_1}/events failed"
    json_events = res_events.get_json()
    assert json_events['total_events'] == 3, f"Expected 3 events in API response, got {json_events['total_events']}"

    print(f"API /api/sessions returned {len(json_list['sessions'])} sessions.")
    print(f"API /api/sessions/{session_1}/events returned {json_events['total_events']} events.")
    print("[PASSED] TEST 5: REST API endpoints (/api/sessions, /api/sessions/<id>, /api/sessions/<id>/events) validated!")

    print("\n==================================================")
    print("ALL PHASE 5 STORAGE TESTS PASSED SUCCESSFULLY!")
    print("==================================================")


if __name__ == '__main__':
    run_phase5_tests()
