"""
Test Suite for Phase 9 - SNORESCAN Advanced Timeline, Graphs & Event History
"""
import os
import time
import unittest
from app import app
from database.db import create_session, end_session, record_snore_event, get_session, get_session_events
from analysis.pattern_analyzer import PatternAnalyzer

class TestPhase9AdvancedAnalysis(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.analyzer = PatternAnalyzer()
        cls.app = app
        cls.client = app.test_client()

    def test_01_zero_event_session(self):
        """Test zero-event session calculations, safety against div-by-zero, NaN, and report endpoints."""
        sess_id = create_session()
        pattern_stats = self.analyzer.analyze_session_events([], session_duration_sec=20.0)

        # Confirm safety values
        self.assertEqual(pattern_stats['total_snores'], 0)
        self.assertEqual(pattern_stats['events_per_minute'], 0.0)
        self.assertEqual(pattern_stats['snoring_percentage'], 0.0)
        self.assertEqual(pattern_stats['quiet_percentage'], 100.0)
        self.assertEqual(pattern_stats['longest_quiet_period'], 20.0)
        self.assertEqual(pattern_stats['strongest_events'], [])
        self.assertEqual(pattern_stats['longest_events'], [])
        self.assertEqual(pattern_stats['event_spacings'], [])

        end_session(sess_id, {'duration_seconds': 20.0, **pattern_stats})

        # Test API response
        resp_events = self.client.get(f"/api/sessions/{sess_id}/events")
        self.assertEqual(resp_events.status_code, 200)
        self.assertEqual(resp_events.get_json()['events'], [])

        resp_adv = self.client.get(f"/api/sessions/{sess_id}/advanced-analysis")
        self.assertEqual(resp_adv.status_code, 200)
        self.assertEqual(resp_adv.get_json()['analysis']['total_snores'], 0)

        # Test CSV Export
        resp_csv = self.client.get(f"/api/sessions/{sess_id}/export/csv")
        self.assertEqual(resp_csv.status_code, 200)
        self.assertIn("Session ID,Event #", resp_csv.get_data(as_text=True))

        # Test Report rendering
        resp_report = self.client.get(f"/report/{sess_id}")
        self.assertEqual(resp_report.status_code, 200)
        self.assertIn("No snoring events detected", resp_report.get_data(as_text=True))
        print("[OK] Test 1: Zero-event session safety & Phase 9 analysis validated.")

    def test_02_one_event_session(self):
        """Test single event session spacing, quiet periods, strongest/longest lists."""
        sess_id = create_session()
        evt = {
            'event_number': 1,
            'start_time': '22:00:05',
            'end_time': '22:00:07',
            'duration_seconds': 2.0,
            'intensity_db': -34.0,
            'peak_amplitude': 0.12,
            'rms_energy': 0.02,
            'dominant_freq_hz': 210.0,
            'confidence': 82.0,
            'spectral_centroid': 650.0,
            'spectral_bandwidth': 950.0,
            'spectral_rolloff': 350.0,
            'spectral_flatness': 0.001,
            'low_frequency_energy': 0.60,
            'mid_frequency_energy': 0.35,
            'high_frequency_energy': 0.05,
            'start_offset_sec': 5.0,
            'time_since_prev_snore': 5.0
        }
        record_snore_event(sess_id, evt)
        events = get_session_events(sess_id)
        self.assertEqual(len(events), 1)

        pattern_stats = self.analyzer.analyze_session_events(events, session_duration_sec=30.0)
        self.assertEqual(pattern_stats['total_snores'], 1)
        self.assertEqual(len(pattern_stats['strongest_events']), 1)
        self.assertEqual(len(pattern_stats['longest_events']), 1)
        self.assertEqual(pattern_stats['quiet_before_first'], 5.0)
        self.assertEqual(pattern_stats['quiet_after_last'], 23.0)  # 30 - (5 + 2)
        self.assertEqual(pattern_stats['longest_quiet_between'], 0.0)

        end_session(sess_id, {'duration_seconds': 30.0, **pattern_stats})

        # Test CSV route
        resp_csv = self.client.get(f"/report/{sess_id}/csv")
        self.assertEqual(resp_csv.status_code, 200)
        self.assertIn("210.0", resp_csv.get_data(as_text=True))
        print("[OK] Test 2: One-event session metrics & export validated.")

    def test_03_multi_event_session_advanced_analysis(self):
        """Test multi-event timeline, spacing, intensity/frequency, quiet periods, and top 3 ranking."""
        sess_id = create_session()

        evts = [
            {
                'event_number': 1,
                'start_time': '22:10:02',
                'end_time': '22:10:03',
                'duration_seconds': 1.0,
                'intensity_db': -42.0,
                'peak_amplitude': 0.07,
                'rms_energy': 0.01,
                'dominant_freq_hz': 150.0,
                'confidence': 70.0,
                'start_offset_sec': 2.0,
                'time_since_prev_snore': 2.0
            },
            {
                'event_number': 2,
                'start_time': '22:10:08',
                'end_time': '22:10:11',
                'duration_seconds': 3.0,
                'intensity_db': -20.0, # Strongest & Longest
                'peak_amplitude': 0.35,
                'rms_energy': 0.08,
                'dominant_freq_hz': 290.0,
                'confidence': 95.0,
                'start_offset_sec': 8.0,
                'time_since_prev_snore': 5.0
            },
            {
                'event_number': 3,
                'start_time': '22:10:16',
                'end_time': '22:10:17.5',
                'duration_seconds': 1.5,
                'intensity_db': -30.0,
                'peak_amplitude': 0.18,
                'rms_energy': 0.03,
                'dominant_freq_hz': 220.0,
                'confidence': 85.0,
                'start_offset_sec': 16.0,
                'time_since_prev_snore': 5.0
            },
            {
                'event_number': 4,
                'start_time': '22:10:25',
                'end_time': '22:10:27',
                'duration_seconds': 2.0,
                'intensity_db': -28.0,
                'peak_amplitude': 0.20,
                'rms_energy': 0.04,
                'dominant_freq_hz': 310.0,
                'confidence': 89.0,
                'start_offset_sec': 25.0,
                'time_since_prev_snore': 7.5
            }
        ]

        for ev in evts:
            record_snore_event(sess_id, ev)

        db_events = get_session_events(sess_id)
        self.assertEqual(len(db_events), 4)

        pattern_stats = self.analyzer.analyze_session_events(db_events, session_duration_sec=40.0)

        # Verify top 3 ranking
        self.assertEqual(len(pattern_stats['strongest_events']), 3)
        self.assertEqual(pattern_stats['strongest_events'][0]['event_number'], 2)  # -20 dBFS
        self.assertEqual(pattern_stats['strongest_events'][1]['event_number'], 4)  # -28 dBFS
        self.assertEqual(pattern_stats['strongest_events'][2]['event_number'], 3)  # -30 dBFS

        self.assertEqual(len(pattern_stats['longest_events']), 3)
        self.assertEqual(pattern_stats['longest_events'][0]['event_number'], 2)   # 3.0s
        self.assertEqual(pattern_stats['longest_events'][1]['event_number'], 4)   # 2.0s
        self.assertEqual(pattern_stats['longest_events'][2]['event_number'], 3)   # 1.5s

        # Verify Spacings:
        # Event 1 start offset 2s, end 3s
        # Event 2 start offset 8s, end 11s -> spacing 8 - 3 = 5s
        # Event 3 start offset 16s, end 17.5s -> spacing 16 - 11 = 5s
        # Event 4 start offset 25s, end 27s -> spacing 25 - 17.5 = 7.5s
        self.assertEqual(len(pattern_stats['event_spacings']), 3)
        self.assertEqual(pattern_stats['event_spacings'][0], 5.0)
        self.assertEqual(pattern_stats['event_spacings'][1], 5.0)
        self.assertEqual(pattern_stats['event_spacings'][2], 7.5)

        # Quiet periods
        self.assertEqual(pattern_stats['quiet_before_first'], 2.0)
        self.assertEqual(pattern_stats['longest_quiet_between'], 7.5)
        self.assertEqual(pattern_stats['quiet_after_last'], 13.0)  # 40 - 27
        self.assertEqual(pattern_stats['longest_quiet_period'], 13.0)

        end_session(sess_id, {'duration_seconds': 40.0, **pattern_stats})

        # Test API response
        resp_adv = self.client.get(f"/api/sessions/{sess_id}/advanced-analysis")
        self.assertEqual(resp_adv.status_code, 200)
        json_data = resp_adv.get_json()['analysis']
        self.assertEqual(json_data['total_snores'], 4)
        self.assertIn('activity_heatmap', json_data)

        # Check Report Page HTML for charts & elements
        resp_report = self.client.get(f"/report/{sess_id}")
        html = resp_report.get_data(as_text=True)
        self.assertEqual(resp_report.status_code, 200)
        self.assertIn("SESSION ACTIVITY SUMMARY", html)
        self.assertIn("LONGEST QUIET PERIOD", html)
        self.assertIn("STRONGEST SNORING EVENTS", html)
        self.assertIn("LONGEST SNORING EVENTS", html)
        self.assertIn("EXPORT SESSION DATA (CSV)", html)
        print("[OK] Test 3: Multi-event session advanced analysis & rankings validated.")

    def test_04_history_page_compatibility(self):
        """Verify history page displays required session metrics and export CSV buttons."""
        resp = self.client.get("/history")
        html = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Snoring %", html)
        self.assertIn("Events/min", html)
        self.assertIn("View Report", html)
        self.assertIn("Export CSV", html)
        print("[OK] Test 4: History page compatibility validated.")

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPhase9AdvancedAnalysis)
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    if result.wasSuccessful():
        print("\nALL PHASE 9 ADVANCED ANALYSIS TESTS PASSED SUCCESSFULLY!")

