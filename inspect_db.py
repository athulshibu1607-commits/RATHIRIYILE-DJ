import sqlite3
import os
import sys

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, 'database', 'snorescan.db')


def inspect_database():
    """Developer inspection tool to dump SQLite sessions and snore_events tables."""
    print("==================================================")
    print("SNORESCAN — SQLITE DATABASE INSPECTION TOOL")
    print("==================================================")
    print(f"Target Database Path: {DB_PATH}")

    if not os.path.exists(DB_PATH):
        print("❌ Database file does not exist yet. Run app.py or init_db() first!")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Inspect sessions table
    print("\n--- SESSIONS TABLE ---")
    cursor.execute("SELECT id, start_time, duration_seconds, total_snores, total_snore_duration, avg_confidence, snore_personality, status FROM sessions ORDER BY id DESC LIMIT 10")
    sessions = cursor.fetchall()
    
    if not sessions:
        print("No session records found.")
    else:
        for s in sessions:
            print(f"Session #{s['id']} | Start: {s['start_time']} | Duration: {s['duration_seconds']:.1f}s | Snores: {s['total_snores']} | Snore Duration: {s['total_snore_duration']:.1f}s | Confidence: {s['avg_confidence']:.1f}% | Personality: '{s['snore_personality']}' | Status: {s['status']}")

    # 2. Inspect snore_events table
    print("\n--- SNORE_EVENTS TABLE (Recent 20 Events) ---")
    cursor.execute("""
        SELECT id, session_id, event_number, start_time, end_time, duration_seconds,
               intensity_db, dominant_freq_hz, spectral_centroid, confidence
        FROM snore_events
        ORDER BY id DESC
        LIMIT 20
    """)
    events = cursor.fetchall()

    if not events:
        print("No snore events recorded in database.")
    else:
        for e in events:
            evt_num = e['event_number'] if 'event_number' in e.keys() else e['id']
            print(f"DB Row #{e['id']} | Session #{e['session_id']} | Event #{evt_num} | Time: {e['start_time']}-{e['end_time']} | Duration: {e['duration_seconds']:.2f}s | Loudness: {e['intensity_db']:.1f} dBFS | Freq: {e['dominant_freq_hz']:.0f} Hz | Centroid: {e['spectral_centroid']:.0f} Hz | Confidence: {e['confidence']:.0f}%")

    conn.close()
    print("\n==================================================")


if __name__ == '__main__':
    inspect_database()
