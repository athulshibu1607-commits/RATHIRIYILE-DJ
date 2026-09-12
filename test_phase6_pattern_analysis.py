import math
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from analysis.pattern_analyzer import PatternAnalyzer
from database.db import init_db, create_session, end_session, record_snore_event


def run_phase6_tests():
    print("==================================================")
    print("SNORESCAN — PHASE 6 PATTERN ANALYSIS TEST SUITE")
    print("==================================================")

    analyzer = PatternAnalyzer()
    init_db()
    client = app.test_client()

    # 1. Test Pattern Analysis on Synthetic Multi-Event Session with Clusters
    print("\n--- TEST 1: Multi-Event Clustered Session Pattern Analysis ---")
    session_duration = 120.0  # 2 minutes

    events = [
        {'id': 1, 'start_offset_sec': 10.0, 'duration_seconds': 0.8, 'intensity_db': -32.0, 'rms_energy': 0.02, 'peak_amplitude': 0.08, 'dominant_freq_hz': 180.0, 'spectral_centroid': 450.0, 'confidence': 85.0},
        {'id': 2, 'start_offset_sec': 14.0, 'duration_seconds': 1.2, 'intensity_db': -30.0, 'rms_energy': 0.025, 'peak_amplitude': 0.09, 'dominant_freq_hz': 175.0, 'spectral_centroid': 440.0, 'confidence': 88.0},
        {'id': 3, 'start_offset_sec': 18.0, 'duration_seconds': 0.9, 'intensity_db': -31.0, 'rms_energy': 0.022, 'peak_amplitude': 0.085, 'dominant_freq_hz': 182.0, 'spectral_centroid': 460.0, 'confidence': 86.0},
        # Long gap of 30s
        {'id': 4, 'start_offset_sec': 50.0, 'duration_seconds': 0.7, 'intensity_db': -35.0, 'rms_energy': 0.018, 'peak_amplitude': 0.07, 'dominant_freq_hz': 240.0, 'spectral_centroid': 600.0, 'confidence': 78.0},
        {'id': 5, 'start_offset_sec': 54.0, 'duration_seconds': 1.1, 'intensity_db': -33.0, 'rms_energy': 0.021, 'peak_amplitude': 0.08, 'dominant_freq_hz': 235.0, 'spectral_centroid': 590.0, 'confidence': 80.0},
    ]

    patterns = analyzer.analyze_session_events(events, session_duration)

    print("Calculated Pattern Metrics:")
    print(f"  Events per Minute: {patterns['events_per_minute']} ({patterns['frequency_classification']})")
    print(f"  Avg Event Spacing: {patterns['avg_event_spacing']}s")
    print(f"  Cluster Count: {patterns['cluster_count']} (Largest Cluster: {patterns['largest_cluster']})")
    print(f"  Duration Pattern: {patterns['duration_pattern']}")
    print(f"  Intensity Pattern: {patterns['intensity_pattern']}")
    print(f"  Frequency Pattern: {patterns['frequency_pattern']}")
    print(f"  Irregular Pattern: {patterns['irregular_pattern']}")
    print(f"  Personality: {patterns['snore_personality']}")
    print(f"  Survival Score: {patterns['survival_score']}/100")
    print("  Acoustic Observations:")
    for obs in patterns['observations']:
        print(f"    {obs}")

    assert patterns['events_per_minute'] > 0.0, "Events per minute should be positive"
    assert patterns['cluster_count'] == 2, f"Expected 2 clusters, got {patterns['cluster_count']}"
    assert patterns['largest_cluster'] == 3, f"Expected largest cluster of 3 events, got {patterns['largest_cluster']}"
    assert len(patterns['observations']) >= 3, "Observations list should contain readable sentences"
    print("[PASSED] TEST 1: Multi-event cluster and pattern analysis calculated accurately!")

    # 2. Test Zero-Event Silent Session
    print("\n--- TEST 2: Zero-Event Silent Session Safety Check ---")
    zero_patterns = analyzer.analyze_session_events([], session_duration_sec=60.0)

    print("Zero-Event Pattern Output:")
    print(f"  Events/Min: {zero_patterns['events_per_minute']}")
    print(f"  Personality: {zero_patterns['snore_personality']}")
    print(f"  Survival Score: {zero_patterns['survival_score']}/100")
    print(f"  Observation: {zero_patterns['observations'][0]}")

    assert zero_patterns['events_per_minute'] == 0.0, "Zero-event events/min should be 0.0"
    assert zero_patterns['cluster_count'] == 0, "Zero-event cluster count should be 0"
    assert zero_patterns['survival_score'] == 100.0, "Zero-event survival score should be 100.0"
    assert "Not enough data" in zero_patterns['observations'][0], "Observation should note insufficient data"
    print("[PASSED] TEST 2: Zero-event silent session handled safely without crashes!")

    # 3. Test REST API Endpoint GET /api/sessions/<id>/patterns
    print("\n--- TEST 3: REST API GET /api/sessions/<id>/patterns Endpoint Check ---")
    session_id = create_session()
    for e in events:
        record_snore_event(session_id, e)
    end_session(session_id, {'duration_seconds': session_duration, 'total_snores': len(events)})

    res = client.get(f'/api/sessions/{session_id}/patterns')
    assert res.status_code == 200, f"GET /api/sessions/{session_id}/patterns failed with status {res.status_code}"
    json_resp = res.get_json()

    print(f"API Response Status: {json_resp['status']}")
    print(f"API Session ID: {json_resp['session_id']}")
    print(f"API Personality: {json_resp['patterns']['snore_personality']}")

    assert json_resp['status'] == 'success', "API status should be success"
    assert json_resp['patterns']['total_snores'] == 5, f"API expected 5 snores, got {json_resp['patterns']['total_snores']}"
    print("[PASSED] TEST 3: GET /api/sessions/<id>/patterns endpoint returned valid JSON pattern payload!")

    print("\n==================================================")
    print("ALL PHASE 6 PATTERN ANALYSIS TESTS PASSED SUCCESSFULLY!")
    print("==================================================")


if __name__ == '__main__':
    run_phase6_tests()
