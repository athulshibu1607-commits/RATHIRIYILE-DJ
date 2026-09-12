"""
Test Suite for Phase 8 - SNORESCAN Complete Session Report
"""
import os
import time
import requests
import unittest
from database.db import create_session, end_session, record_snore_event, get_session, get_session_events
from analysis.pattern_analyzer import PatternAnalyzer

BASE_URL = "http://127.0.0.1:5000"

class TestPhase8SessionReport(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.analyzer = PatternAnalyzer()

    def test_01_zero_event_session(self):
        """Test zero-event session calculations and report page rendering."""
        sess_id = create_session()
        time.sleep(0.5)

        pattern_stats = self.analyzer.analyze_session_events([], session_duration_sec=5.0)
        self.assertEqual(pattern_stats['total_snores'], 0)
        self.assertEqual(pattern_stats['events_per_minute'], 0.0)
        self.assertEqual(pattern_stats['snoring_percentage'], 0.0)
        self.assertEqual(pattern_stats['survival_score'], 100.0)
        self.assertEqual(pattern_stats['shortest_snore'], 0.0)
        self.assertEqual(pattern_stats['min_intensity_db'], -80.0)

        end_session(sess_id, {'duration_seconds': 5.0, **pattern_stats})

        # Fetch report via API / endpoint
        resp = requests.get(f"{BASE_URL}/report/{sess_id}")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("SESSION COMPLETE", resp.text)
        self.assertIn("No possible snoring events detected", resp.text)
        print("[OK] Test 1: Zero-event session safety & report rendering validated.")

    def test_02_one_event_session(self):
        """Test single event session metrics and database persistence."""
        sess_id = create_session()

        evt = {
            'event_number': 1,
            'start_time': '22:00:00',
            'end_time': '22:00:01',
            'duration_seconds': 1.2,
            'intensity_db': -32.5,
            'peak_amplitude': 0.15,
            'rms_energy': 0.02,
            'dominant_freq_hz': 240.0,
            'confidence': 80.0,
            'spectral_centroid': 750.0,
            'spectral_bandwidth': 1100.0,
            'spectral_rolloff': 400.0,
            'spectral_flatness': 0.001,
            'low_frequency_energy': 0.55,
            'mid_frequency_energy': 0.40,
            'high_frequency_energy': 0.05,
            'start_offset_sec': 2.0
        }
        record_snore_event(sess_id, evt)
        events = get_session_events(sess_id)
        self.assertEqual(len(events), 1)

        pattern_stats = self.analyzer.analyze_session_events(events, session_duration_sec=10.0)
        self.assertEqual(pattern_stats['total_snores'], 1)
        self.assertEqual(pattern_stats['shortest_snore'], 1.2)
        self.assertEqual(pattern_stats['longest_snore'], 1.2)
        self.assertEqual(pattern_stats['min_intensity_db'], -32.5)

        end_session(sess_id, {'duration_seconds': 10.0, **pattern_stats})

        resp = requests.get(f"{BASE_URL}/report/{sess_id}")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("240 Hz", resp.text)
        print("[OK] Test 2: One-event session metrics validated.")

    def test_03_multi_event_session(self):
        """Test multi-event session calculations, timeline, and complete metrics."""
        sess_id = create_session()

        evts = [
            {
                'event_number': 1,
                'start_time': '22:05:00',
                'end_time': '22:05:01',
                'duration_seconds': 0.8,
                'intensity_db': -40.0,
                'peak_amplitude': 0.08,
                'rms_energy': 0.01,
                'dominant_freq_hz': 180.0,
                'confidence': 75.0,
                'start_offset_sec': 5.0
            },
            {
                'event_number': 2,
                'start_time': '22:05:08',
                'end_time': '22:05:10',
                'duration_seconds': 1.6,
                'intensity_db': -25.0,
                'peak_amplitude': 0.22,
                'rms_energy': 0.04,
                'dominant_freq_hz': 320.0,
                'confidence': 88.0,
                'start_offset_sec': 13.0
            }
        ]

        for ev in evts:
            record_snore_event(sess_id, ev)

        db_events = get_session_events(sess_id)
        self.assertEqual(len(db_events), 2)  # No duplicates

        pattern_stats = self.analyzer.analyze_session_events(db_events, session_duration_sec=30.0)
        self.assertEqual(pattern_stats['total_snores'], 2)
        self.assertEqual(pattern_stats['shortest_snore'], 0.8)
        self.assertEqual(pattern_stats['longest_snore'], 1.6)
        self.assertEqual(pattern_stats['min_intensity_db'], -40.0)
        self.assertEqual(pattern_stats['max_intensity_db'], -25.0)

        end_session(sess_id, {'duration_seconds': 30.0, **pattern_stats})

        # Check database record
        saved_sess = get_session(sess_id)
        self.assertEqual(saved_sess['status'], 'completed')
        self.assertEqual(saved_sess['total_snores'], 2)

        resp = requests.get(f"{BASE_URL}/report/{sess_id}")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Complete Event-by-Event Acoustic Metrics", resp.text)
        print("[OK] Test 3: Multi-event session & timeline validated.")

    def test_04_no_duplicate_events_or_sessions(self):
        """Verify database integrity - no duplicate events or session entries."""
        sess_id = create_session()
        evt = {
            'event_number': 1,
            'start_time': '22:10:00',
            'end_time': '22:10:01',
            'duration_seconds': 1.0,
            'intensity_db': -30.0,
            'dominant_freq_hz': 250.0
        }
        record_snore_event(sess_id, evt)

        events = get_session_events(sess_id)
        self.assertEqual(len(events), 1)

        end_session(sess_id, {'duration_seconds': 10.0, 'total_snores': 1})
        events_after = get_session_events(sess_id)
        self.assertEqual(len(events_after), 1)
        print("[OK] Test 4: Database integrity & deduplication verified.")

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPhase8SessionReport)
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    if result.wasSuccessful():
        print("\nALL PHASE 8 SESSION REPORT TESTS PASSED SUCCESSFULLY!")
