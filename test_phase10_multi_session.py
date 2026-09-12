"""
Test Suite for Phase 10 - SNORESCAN Multi-Session History, Comparison & Trends
"""
import os
import unittest
from app import app
from database.db import create_session, end_session, record_snore_event, get_session, get_session_events, get_all_sessions
from analysis.pattern_analyzer import PatternAnalyzer

class TestPhase10MultiSession(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.analyzer = PatternAnalyzer()
        cls.app = app
        cls.client = app.test_client()

    def test_01_empty_database_and_single_session_safety(self):
        """Test empty database state and single session fallback behavior."""
        # 1. Test APIs with empty database or 0 sessions
        trends = self.analyzer.calculate_trends()
        self.assertEqual(trends['status'], 'success')

        stats = self.analyzer.calculate_overall_statistics()
        self.assertIn('total_sessions', stats)

        comp = self.analyzer.compare_sessions([])
        self.assertEqual(comp['status'], 'error')
        self.assertEqual(comp['message'], 'Select at least 2 sessions to compare.')

        # 2. Test 1 session state
        s1 = create_session()
        evt1 = {
            'event_number': 1,
            'start_time': '23:00:00',
            'end_time': '23:00:02',
            'duration_seconds': 2.0,
            'intensity_db': -35.0,
            'dominant_freq_hz': 220.0,
            'confidence': 85.0
        }
        record_snore_event(s1, evt1)
        end_session(s1, {'duration_seconds': 30.0, 'total_snores': 1, 'snoring_percentage': 6.7, 'avg_intensity_db': -35.0})

        # Single session comparison attempt
        comp_one = self.analyzer.compare_sessions([s1])
        self.assertEqual(comp_one['status'], 'error')

        # Single session / DB trend API
        resp_trend = self.client.get('/api/sessions/trends')
        self.assertEqual(resp_trend.status_code, 200)
        self.assertIn('has_trends', resp_trend.get_json())

        # Render compare route with 1 session
        resp_comp_page = self.client.get(f'/compare?ids={s1}')
        self.assertEqual(resp_comp_page.status_code, 200)
        self.assertIn("Select at least 2 sessions to compare", resp_comp_page.get_data(as_text=True))
        print("[OK] Test 1: Empty DB & single session fallback safety validated.")

    def test_02_multi_session_comparison_and_rankings(self):
        """Test multi-session comparison table, SNORE BATTLE, change analysis, and rankings."""
        # Create Session A (Moderate)
        sa = create_session()
        record_snore_event(sa, {
            'event_number': 1, 'start_time': '23:10:00', 'end_time': '23:10:01', 'duration_seconds': 1.0,
            'intensity_db': -40.0, 'dominant_freq_hz': 180.0, 'confidence': 75.0, 'time_since_prev_snore': 5.0
        })
        stats_a = self.analyzer.analyze_session_events(get_session_events(sa), 30.0)
        end_session(sa, {'duration_seconds': 30.0, **stats_a})

        # Create Session B (Heavy / Active)
        sb = create_session()
        for idx in range(1, 4):
            record_snore_event(sb, {
                'event_number': idx, 'start_time': f'23:20:0{idx*2}', 'end_time': f'23:20:0{idx*2+1}', 'duration_seconds': 2.5,
                'intensity_db': -22.0, 'dominant_freq_hz': 310.0, 'confidence': 92.0, 'time_since_prev_snore': 4.0
            })
        stats_b = self.analyzer.analyze_session_events(get_session_events(sb), 30.0)
        end_session(sb, {'duration_seconds': 30.0, **stats_b})

        # Compare Sessions A and B
        res = self.analyzer.compare_sessions([sa, sb])
        self.assertEqual(res['status'], 'success')
        self.assertEqual(len(res['sessions']), 2)

        # Verify SNORE BATTLE winner (Session B is heavier)
        self.assertEqual(res['snore_battle']['winner_session_id'], sb)
        self.assertIn("SNORE BATTLE", res['snore_battle']['verdict'])

        # Verify Roommate Survival (Session A is quieter, so better survival)
        self.assertEqual(res['roommate_survival_comparison']['best_session_id'], sa)

        # Verify Session Change calculation
        self.assertEqual(len(res['changes']), 1)
        chg = res['changes'][0]
        self.assertEqual(chg['from_session'], sa)
        self.assertEqual(chg['to_session'], sb)
        self.assertEqual(chg['trend_direction'], 'increased')
        self.assertIn("Acoustic activity increased", chg['neutral_wording'])

        # Test Compare API Endpoint
        resp_api = self.client.get(f'/api/sessions/compare?ids={sa},{sb}')
        self.assertEqual(resp_api.status_code, 200)
        self.assertEqual(len(resp_api.get_json()['sessions']), 2)

        # Test Invalid IDs API handling
        resp_invalid = self.client.get('/api/sessions/compare?ids=99999,88888')
        self.assertEqual(resp_invalid.status_code, 400)
        self.assertEqual(resp_invalid.get_json()['status'], 'error')

        # Test CSV Export Endpoint
        resp_csv = self.client.get(f'/compare/csv?ids={sa},{sb}')
        self.assertEqual(resp_csv.status_code, 200)
        csv_text = resp_csv.get_data(as_text=True)
        self.assertIn("Session ID,Date,Duration", csv_text)
        self.assertIn(str(sa), csv_text)
        self.assertIn(str(sb), csv_text)
        print("[OK] Test 2: Multi-session comparison, SNORE BATTLE & CSV export validated.")

    def test_03_all_time_statistics_and_best_worst(self):
        """Test all-time statistics, most active, quietest, and most intense sessions."""
        overall_stats = self.analyzer.calculate_overall_statistics()
        self.assertGreaterEqual(overall_stats['total_sessions'], 2)
        self.assertIsNotNone(overall_stats['most_active_session'])
        self.assertIsNotNone(overall_stats['quietest_session'])
        self.assertIsNotNone(overall_stats['most_intense_session'])

        # Test Statistics API Endpoint
        resp_stats = self.client.get('/api/sessions/statistics')
        self.assertEqual(resp_stats.status_code, 200)
        data = resp_stats.get_json()['statistics']
        self.assertIn('total_sessions', data)
        self.assertIn('overall_avg_snoring_percentage', data)
        print("[OK] Test 3: All-time statistics & best/worst session rankings validated.")

    def test_04_history_page_selection_and_ui(self):
        """Test history page rendered HTML contains selection checkboxes and compare link."""
        resp = self.client.get('/history')
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn('session-cb', html)
        self.assertIn('COMPARE SELECTED SESSIONS', html)
        self.assertIn('submitComparison()', html)
        print("[OK] Test 4: History page selection checkboxes & compare action validated.")

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPhase10MultiSession)
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    if result.wasSuccessful():
        print("\nALL PHASE 10 MULTI-SESSION TESTS PASSED SUCCESSFULLY!")
