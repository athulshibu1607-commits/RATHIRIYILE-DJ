"""
Test Suite for Phase 7 - SNORESCAN Live Monitoring Dashboard
"""
import time
import requests
import unittest

BASE_URL = "http://127.0.0.1:5000"

class TestPhase7LiveDashboard(unittest.TestCase):

    def test_01_idle_status(self):
        """Test GET /api/monitoring/status when idle."""
        resp = requests.get(f"{BASE_URL}/api/monitoring/status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        
        # Verify required Phase 7 fields exist
        self.assertIn("monitoring", data)
        self.assertIn("duration", data)
        self.assertIn("event_count", data)
        self.assertIn("snoring_duration", data)
        self.assertIn("snoring_percentage", data)
        self.assertIn("average_intensity", data)
        self.assertIn("latest_frequency", data)
        self.assertIn("min_frequency", data)
        self.assertIn("max_frequency", data)
        self.assertIn("events", data)
        self.assertIn("intensity_history", data)
        self.assertIsInstance(data["events"], list)
        self.assertIsInstance(data["intensity_history"], list)
        print("[OK] Idle status payload validated.")

    def test_02_live_session_lifecycle(self):
        """Test start monitoring -> poll status -> stop monitoring -> verify report redirect."""
        # 1. Start monitoring
        start_resp = requests.post(f"{BASE_URL}/api/monitoring/start")
        self.assertEqual(start_resp.status_code, 200)
        start_data = start_resp.json()
        self.assertEqual(start_data.get("status"), "success")
        session_id = start_data.get("session_id")
        self.assertIsNotNone(session_id)
        print(f"[OK] Started Live Monitoring Session #{session_id}")

        # 2. Poll live status while monitoring
        time.sleep(2.0)
        status_resp = requests.get(f"{BASE_URL}/api/monitoring/status")
        self.assertEqual(status_resp.status_code, 200)
        status_data = status_resp.json()
        self.assertTrue(status_data.get("monitoring"))
        self.assertEqual(status_data.get("session_id"), session_id)
        self.assertGreater(status_data.get("duration", 0), 0)
        print(f"[OK] Polled active monitoring status: Duration={status_data.get('duration')}s, Events={status_data.get('event_count')}")

        # 3. Stop monitoring
        stop_resp = requests.post(f"{BASE_URL}/api/monitoring/stop", json={"session_id": session_id})
        self.assertEqual(stop_resp.status_code, 200)
        stop_data = stop_resp.json()
        self.assertEqual(stop_data.get("status"), "success")
        print(f"[OK] Stopped Monitoring Session #{session_id}")

        # 4. Verify Session Report loads cleanly with Phase 6 analysis & Phase 4 metrics
        report_resp = requests.get(f"{BASE_URL}/report/{session_id}")
        self.assertEqual(report_resp.status_code, 200)
        self.assertIn("Advanced Graphical Signal Analysis", report_resp.text)
        print(f"[OK] Session Report /report/{session_id} validated successfully.")

if __name__ == '__main__':
    unittest.main()
