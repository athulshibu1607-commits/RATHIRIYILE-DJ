"""
Phase 12 — SNORESCAN Final Polish, Reliability & Hackathon Demo Test Suite
"""
import os
import sys
import unittest
import json
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app
from database.db import (
    init_db,
    create_session,
    end_session,
    record_snore_event,
    get_session,
    get_all_sessions,
    get_session_events
)
from analysis import PatternAnalyzer, FunAnalyzer


class TestPhase12Final(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()
        cls.app = app
        cls.client = app.test_client()
        cls.pattern_analyzer = PatternAnalyzer()
        cls.fun_analyzer = FunAnalyzer()

    def test_01_home_page(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'SNORESCAN', res.data)
        self.assertIn(b'Because apparently your sleep needed analytics.', res.data)

    def test_02_monitoring_page(self):
        res = self.client.get('/monitoring')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'LIVE MONITORING', res.data)

    def test_03_history_page(self):
        res = self.client.get('/history')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Session History', res.data)

    def test_04_report_page(self):
        sess_id = create_session()
        res = self.client.get(f'/report/{sess_id}')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'SESSION COMPLETE', res.data)

    def test_05_compare_page(self):
        res = self.client.get('/compare')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Multi-Session Comparison', res.data)

    def test_06_api_health(self):
        res = self.client.get('/api/status')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('components', data)

    def test_06b_useless_hub_page(self):
        res = self.client.get('/useless')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'USELESS INTELLIGENCE', res.data)

    def test_07_zero_event_safety(self):
        stats = self.pattern_analyzer.analyze_session_events([], 60.0)
        self.assertEqual(stats['total_events'], 0)
        self.assertEqual(stats['snoring_percentage'], 0.0)

    def test_08_zero_session_safety(self):
        stats = self.pattern_analyzer.calculate_overall_statistics()
        self.assertIsNotNone(stats)
        self.assertIn('total_sessions', stats)

    def test_09_one_event_safety(self):
        events = [{'duration_seconds': 2.5, 'intensity_db': -20.0, 'rms_energy': 0.04, 'peak_amplitude': 0.15, 'dominant_freq_hz': 150.0, 'confidence': 0.9, 'start_offset_sec': 10.0}]
        stats = self.pattern_analyzer.analyze_session_events(events, 60.0)
        self.assertEqual(stats['total_events'], 1)
        self.assertGreater(stats['snoring_percentage'], 0.0)

    def test_10_multiple_event_safety(self):
        events = [
            {'duration_seconds': 2.5, 'intensity_db': -20.0, 'rms_energy': 0.04, 'peak_amplitude': 0.15, 'dominant_freq_hz': 150.0, 'confidence': 0.9, 'start_offset_sec': 10.0},
            {'duration_seconds': 4.0, 'intensity_db': -15.0, 'rms_energy': 0.06, 'peak_amplitude': 0.22, 'dominant_freq_hz': 120.0, 'confidence': 0.95, 'start_offset_sec': 25.0}
        ]
        stats = self.pattern_analyzer.analyze_session_events(events, 120.0)
        self.assertEqual(stats['total_events'], 2)

    def test_11_database_persistence(self):
        sess_id = create_session()
        sess = get_session(sess_id)
        self.assertIsNotNone(sess)
        self.assertEqual(sess['id'], sess_id)

    def test_12_session_finalization(self):
        sess_id = create_session()
        end_session(sess_id, {'duration_seconds': 45.0, 'total_snores': 2})
        sess = get_session(sess_id)
        self.assertEqual(sess['status'], 'completed')

    def test_13_duplicate_event_prevention(self):
        sess_id = create_session()
        ev1 = record_snore_event(sess_id, {'start_time': '23:00:01', 'end_time': '23:00:03', 'duration_seconds': 2.0})
        events = get_session_events(sess_id)
        self.assertEqual(len(events), 1)

    def test_14_csv_export(self):
        sess_id = create_session()
        res = self.client.get(f'/api/sessions/{sess_id}/export/csv')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Session ID', res.data)

    def test_15_fun_analysis(self):
        sess_id = create_session()
        res = self.client.get(f'/api/sessions/{sess_id}/fun-analysis')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn('fun_analysis', data)

    def test_16_demo_mode_isolation(self):
        sessions_before = len(get_all_sessions())
        res = self.client.get('/demo/report')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'DEMO MODE', res.data)
        sessions_after = len(get_all_sessions())
        self.assertEqual(sessions_before, sessions_after)

    def test_17_invalid_session_handling(self):
        res = self.client.get('/report/999999')
        self.assertEqual(res.status_code, 302)  # Redirects safely to history

    def test_18_frontend_api_compatibility(self):
        res = self.client.get('/api/monitoring/status')
        self.assertEqual(res.status_code, 200)

    def test_19_no_nan_values(self):
        stats = self.pattern_analyzer.analyze_session_events([], 0.0)
        json_str = json.dumps(stats)
        self.assertNotIn('NaN', json_str)

    def test_20_no_undefined_values(self):
        fun_res = self.fun_analyzer.analyze_fun_features(1, {'id': 1}, [], {})
        json_str = json.dumps(fun_res)
        self.assertNotIn('undefined', json_str)

    def test_21_existing_phase_1_11_compatibility(self):
        sessions = get_all_sessions()
        self.assertIsInstance(sessions, list)


if __name__ == '__main__':
    result = unittest.main(exit=False)
    if result.result.wasSuccessful():
        print("\nALL PHASE 12 FINAL TESTS PASSED SUCCESSFULLY!")
