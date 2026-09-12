"""
Unit tests for SNORESCAN Phase 13 — Day/Night Engine & Interactive Snore Boss Game.
"""

import unittest
from app import app, boss_analyzer
from database import init_db, create_session, end_session, record_snore_event


class TestPhase13DayNight(unittest.TestCase):
    """Test suite for Phase 13 Snore Boss, Snore Court, Trivia, and API safety."""

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        with app.app_context():
            init_db()

    def test_boss_generator_determinism(self):
        """Verify boss stats generation is 100% deterministic for a given session."""
        session_id = create_session()
        record_snore_event(session_id, {
            'event_number': 1,
            'start_time': '00:00:00',
            'end_time': '00:00:05',
            'duration_seconds': 5.0,
            'intensity_db': -20.0,
            'peak_amplitude': 0.15,
            'rms_energy': 0.04,
            'dominant_freq_hz': 150.0,
            'confidence': 95.0
        })
        end_session(session_id, {
            'duration_seconds': 30.0,
            'total_chunks': 15,
            'total_snores': 1,
            'total_snore_duration': 5.0,
            'avg_snore_duration': 5.0,
            'longest_snore': 5.0,
            'avg_intensity_db': -20.0,
            'max_intensity_db': -20.0,
            'avg_rms': 0.04,
            'max_peak': 0.15,
            'dominant_freq_hz': 150.0
        })

        session = {'id': session_id, 'duration_seconds': 30.0}
        stats = {'total_snores': 1, 'max_intensity_db': -20.0, 'total_snore_duration': 5.0, 'dominant_freq_hz': 150.0}
        events = [{'event_number': 1, 'duration_seconds': 5.0, 'intensity_db': -20.0, 'dominant_freq_hz': 150.0}]

        boss1 = boss_analyzer.generate_boss(session_id, session, stats, events)
        boss2 = boss_analyzer.generate_boss(session_id, session, stats, events)

        self.assertEqual(boss1['name'], boss2['name'])
        self.assertEqual(boss1['level'], boss2['level'])
        self.assertEqual(boss1['max_hp'], boss2['max_hp'])
        self.assertEqual(boss1['boss_power'], boss2['boss_power'])

    def test_zero_event_session_boss(self):
        """Verify zero-event sessions produce a safe sleeping minion without throwing errors."""
        session_id = create_session()
        end_session(session_id, {
            'duration_seconds': 10.0,
            'total_chunks': 5,
            'total_snores': 0,
            'total_snore_duration': 0.0,
            'avg_snore_duration': 0.0,
            'longest_snore': 0.0,
            'avg_intensity_db': -80.0,
            'max_intensity_db': -80.0,
            'avg_rms': 0.0,
            'max_peak': 0.0,
            'dominant_freq_hz': 0.0
        })

        session = {'id': session_id, 'duration_seconds': 10.0}
        stats = {'total_snores': 0, 'max_intensity_db': -80.0, 'total_snore_duration': 0.0, 'dominant_freq_hz': 0.0}
        events = []

        boss = boss_analyzer.generate_boss(session_id, session, stats, events)
        self.assertTrue(boss['is_sleeping'])
        self.assertEqual(boss['level'], 1)
        self.assertGreater(boss['max_hp'], 0)

    def test_snore_court_verdicts(self):
        """Verify Snore Court generates verdicts for all supported culprits."""
        culprits = ["ME", "MY ROOMMATE", "THE DOG", "A GHOST", "ALIENS", "UNKNOWN ENTITY"]
        for culprit in culprits:
            verdict = boss_analyzer.get_snore_court_verdict(culprit)
            self.assertEqual(verdict['culprit'], culprit)
            self.assertIn("VERDICT", verdict['sentence'])

    def test_guess_the_snore_trivia(self):
        """Verify Trivia generation logic for both zero-event and multi-event sessions."""
        events = [
            {'event_index': 1, 'duration_seconds': 4.2, 'intensity_db': -18.5, 'dominant_freq_hz': 140.0}
        ]
        trivia = boss_analyzer.get_guess_the_snore_trivia(101, events)
        self.assertTrue(trivia['has_events'])
        self.assertEqual(len(trivia['options']), 4)

        # Zero events fallback
        trivia_zero = boss_analyzer.get_guess_the_snore_trivia(102, [])
        self.assertFalse(trivia_zero['has_events'])
        self.assertEqual(len(trivia_zero['options']), 4)

    def test_hall_of_shame(self):
        """Verify Hall of Shame leaderboards query returns valid records."""
        session_id = create_session()
        record_snore_event(session_id, {
            'event_number': 1,
            'start_time': '00:00:00',
            'end_time': '00:00:03',
            'duration_seconds': 3.0,
            'intensity_db': -15.0,
            'peak_amplitude': 0.2,
            'rms_energy': 0.05,
            'dominant_freq_hz': 160.0,
            'confidence': 95.0
        })
        end_session(session_id, {
            'duration_seconds': 20.0,
            'total_chunks': 10,
            'total_snores': 1,
            'total_snore_duration': 3.0,
            'avg_snore_duration': 3.0,
            'longest_snore': 3.0,
            'avg_intensity_db': -15.0,
            'max_intensity_db': -15.0,
            'avg_rms': 0.05,
            'max_peak': 0.2,
            'dominant_freq_hz': 160.0
        })

        shame = boss_analyzer.get_hall_of_shame()
        self.assertIsNotNone(shame['most_snores'])
        self.assertIsNotNone(shame['loudest'])

    def test_api_boss_endpoints(self):
        """Verify API endpoints /api/boss/<session_id> and /api/boss/court return 200 OK."""
        session_id = create_session()
        record_snore_event(session_id, {
            'event_number': 1,
            'start_time': '00:00:00',
            'end_time': '00:00:02',
            'duration_seconds': 2.0,
            'intensity_db': -25.0,
            'peak_amplitude': 0.1,
            'rms_energy': 0.03,
            'dominant_freq_hz': 140.0,
            'confidence': 90.0
        })
        end_session(session_id, {
            'duration_seconds': 15.0,
            'total_chunks': 8,
            'total_snores': 1,
            'total_snore_duration': 2.0,
            'avg_snore_duration': 2.0,
            'longest_snore': 2.0,
            'avg_intensity_db': -25.0,
            'max_intensity_db': -25.0,
            'avg_rms': 0.03,
            'max_peak': 0.1,
            'dominant_freq_hz': 140.0
        })

        response = self.app.get(f'/api/boss/{session_id}')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('boss', data)

        court_res = self.app.get('/api/boss/court?culprit=ALIENS')
        self.assertEqual(court_res.status_code, 200)
        court_data = court_res.get_json()
        self.assertEqual(court_data['culprit'], 'ALIENS')

    def test_no_transition_overlays(self):
        """Verify that zero transition overlays, modals, or announcement screens exist in the HTML output."""
        pages = ['/', '/monitoring', '/useless', '/demo']
        for page in pages:
            res = self.app.get(page)
            self.assertEqual(res.status_code, 200)
            self.assertNotIn(b'cinematic-overlay', res.data)
            self.assertNotIn(b'THE NIGHT IS COMING', res.data)
            self.assertNotIn(b'THE DAY IS OVER', res.data)


if __name__ == '__main__':
    unittest.main()

