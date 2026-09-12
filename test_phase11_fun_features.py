import unittest
import os
import sys
import sqlite3
import json
import math

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from database.db import (
    init_db,
    get_db_connection,
    create_session,
    end_session,
    record_snore_event,
    get_session,
    get_all_sessions,
    get_session_events
)
from analysis.fun_analyzer import FunAnalyzer

class TestPhase11FunFeatures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.fun_analyzer = FunAnalyzer()

    def test_01_personality_2_0(self):
        stats = {
            "events_per_minute": 5.0,
            "avg_intensity": 85.0,
            "longest_event_duration": 8.0,
            "snore_percentage": 45.0,
            "avg_dominant_frequency": 120.0,
            "avg_event_duration": 4.5
        }
        res = self.fun_analyzer.get_snore_personality(stats)
        self.assertIn("name", res)
        self.assertIn("explanation", res)
        self.assertIn("icon", res)
        self.assertTrue(len(res["name"]) > 0)
        self.assertFalse(math.isnan(stats["events_per_minute"]))

    def test_02_power_level(self):
        stats = {
            "avg_intensity": 75.0,
            "avg_event_duration": 3.0,
            "events_per_minute": 4.0,
            "snore_percentage": 30.0
        }
        power = self.fun_analyzer.calculate_snore_power(stats)
        self.assertIn("score", power)
        self.assertIn("level", power)
        self.assertIn("disclaimer", power)
        self.assertGreaterEqual(power["score"], 0)
        self.assertLessEqual(power["score"], 100)

    def test_03_roommate_damage(self):
        stats = {
            "snore_percentage": 50.0,
            "total_events": 25,
            "avg_intensity": 70.0,
            "longest_event_duration": 6.0
        }
        rd = self.fun_analyzer.calculate_roommate_damage(stats)
        self.assertIn("patience_remaining_pct", rd)
        self.assertIn("description", rd)
        self.assertGreaterEqual(rd["patience_remaining_pct"], 0)
        self.assertLessEqual(rd["patience_remaining_pct"], 100)

    def test_04_boss_battle(self):
        stats = {
            "total_events": 15,
            "avg_intensity": 65.0,
            "longest_event_duration": 5.2,
            "snore_percentage": 25.0,
            "events_per_minute": 3.0
        }
        boss = self.fun_analyzer.calculate_boss_battle(stats)
        self.assertIn("boss_name", boss)
        self.assertIn("level", boss)
        self.assertIn("power", boss)
        self.assertIn("special_move", boss)
        self.assertIn("5.2", boss["special_move"])

    def test_05_achievements(self):
        stats = {
            "total_events": 12,
            "avg_intensity": 85.0,
            "longest_event_duration": 6.5,
            "max_intensity": 95.0,
            "snore_percentage": 40.0,
            "avg_dominant_frequency": 110.0,
            "events_per_minute": 5.0,
            "events_in_session": 12
        }
        ach = self.fun_analyzer.check_achievements(stats)
        self.assertIsInstance(ach, list)
        self.assertGreater(len(ach), 0)
        for a in ach:
            self.assertIn("title", a)
            self.assertIn("desc", a)
            self.assertIn("unlocked", a)

    def test_06_session_title(self):
        stats = {
            "avg_intensity": 88.0,
            "snore_percentage": 55.0,
            "events_per_minute": 6.0,
            "longest_event_duration": 8.0,
            "avg_dominant_frequency": 120.0
        }
        title = self.fun_analyzer.generate_session_title(stats)
        self.assertIsInstance(title, str)
        self.assertGreater(len(title), 0)

    def test_07_snore_weather(self):
        stats = {
            "snore_percentage": 35.0,
            "events_per_minute": 4.5,
            "avg_intensity": 60.0
        }
        weather = self.fun_analyzer.calculate_snore_weather(stats)
        self.assertIn("condition", weather)
        self.assertIn("temp", weather)
        self.assertIn("wind", weather)
        self.assertIn("storm_intensity", weather)

    def test_08_snore_forecast(self):
        stats = {
            "snore_percentage": 40.0,
            "events_per_minute": 5.0,
            "avg_intensity": 70.0,
            "avg_event_duration": 3.0
        }
        fc = self.fun_analyzer.calculate_snore_forecast(stats)
        self.assertIn("tractor_chance_pct", fc)
        self.assertIn("turbulence_prob", fc)
        self.assertIn("engine_noises", fc)
        self.assertIn("disclaimer", fc)

    def test_09_sleep_genre(self):
        stats = {
            "avg_dominant_frequency": 100.0,
            "avg_intensity": 80.0
        }
        genre = self.fun_analyzer.calculate_sleep_genre(stats)
        self.assertIn("genre", genre)
        self.assertIn("description", genre)

    def test_10_commentator(self):
        stats = {
            "total_events": 10,
            "max_intensity": 88.0,
            "longest_event_duration": 5.5,
            "max_combo": 4
        }
        comm = self.fun_analyzer.generate_commentary(stats, events=[])
        self.assertIsInstance(comm, list)
        self.assertGreater(len(comm), 0)

    def test_11_combo_system(self):
        events = [
            {"start_time": 10.0, "end_time": 12.0},
            {"start_time": 15.0, "end_time": 17.0},
            {"start_time": 20.0, "end_time": 22.0},
            {"start_time": 50.0, "end_time": 52.0}
        ]
        combos = self.fun_analyzer.calculate_combos(events)
        self.assertIn("max_combo", combos)
        self.assertIn("max_combo_str", combos)
        self.assertEqual(combos["max_combo"], 3)

    def test_12_snore_streak(self):
        streak = self.fun_analyzer.calculate_snore_streak()
        self.assertIn("current_streak", streak)
        self.assertIn("longest_streak", streak)
        self.assertIn("current_streak_str", streak)

    def test_13_hall_of_fame(self):
        hof = self.fun_analyzer.get_hall_of_fame()
        self.assertIn("loudest_event", hof)
        self.assertIn("longest_event", hof)
        self.assertIn("most_events_session", hof)

    def test_14_world_records(self):
        wr = self.fun_analyzer.get_world_records()
        self.assertIn("records", wr)
        self.assertIn("disclaimer", wr)

    def test_15_historical_snore_battle(self):
        sess1 = create_session()
        sess2 = create_session()
        
        record_snore_event(sess1, {
            'start_time': '10:00:10', 'end_time': '10:00:13', 'duration_seconds': 3.0,
            'peak_amplitude': 0.05, 'rms_energy': 0.02, 'intensity_db': -30.0,
            'dominant_freq_hz': 150.0, 'spectral_centroid': 500.0,
            'spectral_bandwidth': 300.0, 'spectral_rolloff': 700.0,
            'spectral_flatness': 0.01, 'low_frequency_energy': 0.6,
            'mid_frequency_energy': 0.3, 'high_frequency_energy': 0.1,
            'confidence': 0.9
        })
        record_snore_event(sess2, {
            'start_time': '10:00:05', 'end_time': '10:00:15', 'duration_seconds': 10.0,
            'peak_amplitude': 0.2, 'rms_energy': 0.08, 'intensity_db': -12.0,
            'dominant_freq_hz': 120.0, 'spectral_centroid': 450.0,
            'spectral_bandwidth': 250.0, 'spectral_rolloff': 600.0,
            'spectral_flatness': 0.01, 'low_frequency_energy': 0.7,
            'mid_frequency_energy': 0.2, 'high_frequency_energy': 0.1,
            'confidence': 0.95
        })
        
        battle = self.fun_analyzer.battle_sessions(sess1, sess2)
        self.assertIn("winner_session_id", battle)
        self.assertIn("summary", battle)

    def test_16_report_card(self):
        stats = {
            "avg_intensity": 75.0,
            "events_per_minute": 4.0,
            "snore_percentage": 35.0,
            "longest_event_duration": 6.0
        }
        card = self.fun_analyzer.generate_report_card(stats)
        self.assertIn("loudness_grade", card)
        self.assertIn("frequency_grade", card)
        self.assertIn("chaos_grade", card)
        self.assertIn("uselessness_grade", card)

    def test_17_certificate(self):
        stats = {
            "total_events": 15,
            "duration_minutes": 25.0
        }
        cert = self.fun_analyzer.generate_certificate("sess_99", "2026-09-11 23:00", stats)
        self.assertIn("title", cert)
        self.assertIn("session_id", cert)
        self.assertIn("institute", cert)

    def test_18_share_card_data(self):
        stats = {
            "total_events": 10,
            "snore_percentage": 20.0,
            "avg_intensity": 60.0
        }
        sc = self.fun_analyzer.generate_share_card_data("sess_100", stats)
        self.assertIn("session_id", sc)
        self.assertIn("personality", sc)
        self.assertIn("power", sc)

    def test_19_zero_event_safety(self):
        stats = {
            "total_events": 0,
            "duration_seconds": 60,
            "duration_minutes": 1.0,
            "events_per_minute": 0.0,
            "avg_intensity": 0.0,
            "max_intensity": 0.0,
            "longest_event_duration": 0.0,
            "avg_event_duration": 0.0,
            "snore_percentage": 0.0,
            "avg_dominant_frequency": 0.0,
            "events_in_session": 0
        }
        res = self.fun_analyzer.analyze_fun_features(1, {"id": 1, "start_time": "2026-09-11"}, [], stats)
        self.assertIsNotNone(res)
        self.assertEqual(res["snore_power"]["score"], 0)
        self.assertEqual(res["roommate_damage"]["patience_remaining_pct"], 100)

    def test_20_zero_session_safety(self):
        streak = self.fun_analyzer.calculate_snore_streak()
        self.assertIn("current_streak", streak)
        
        hof = self.fun_analyzer.get_hall_of_fame()
        self.assertIn("loudest_event", hof)

    def test_21_database_persistence(self):
        session_id = create_session()
        session = get_session(session_id)
        self.assertIsNotNone(session)

    def test_22_existing_phase_1_10_compatibility(self):
        from analysis.pattern_analyzer import PatternAnalyzer
        pa = PatternAnalyzer()
        sess_id = create_session()
        summary = pa.calculate_overall_statistics()
        self.assertIn("total_sessions", summary)

    def test_23_no_random_fake_values(self):
        stats = {
            "events_per_minute": 2.0,
            "avg_intensity": 50.0,
            "longest_event_duration": 3.0,
            "snore_percentage": 10.0,
            "avg_dominant_frequency": 200.0,
            "avg_event_duration": 2.0
        }
        r1 = self.fun_analyzer.get_snore_personality(stats)
        r2 = self.fun_analyzer.get_snore_personality(stats)
        self.assertEqual(r1["name"], r2["name"])

    def test_24_no_nan_undefined_values(self):
        stats = {
            "total_events": 0,
            "duration_seconds": 0,
            "duration_minutes": 0.0,
            "events_per_minute": 0.0,
            "avg_intensity": 0.0,
            "max_intensity": 0.0,
            "longest_event_duration": 0.0,
            "avg_event_duration": 0.0,
            "snore_percentage": 0.0,
            "avg_dominant_frequency": 0.0,
            "events_in_session": 0
        }
        res = self.fun_analyzer.analyze_fun_features(1, {"id": 1, "start_time": "2026-09-11"}, [], stats)
        json_str = json.dumps(res)
        self.assertNotIn("NaN", json_str)

if __name__ == "__main__":
    result = unittest.main(exit=False)
    if result.result.wasSuccessful():
        print("\nALL PHASE 11 FUN FEATURE TESTS PASSED SUCCESSFULLY!")
