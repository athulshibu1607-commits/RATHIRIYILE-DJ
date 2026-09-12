import os
import sqlite3
import logging
from datetime import datetime

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, 'snorescan.db')
SCHEMA_PATH = os.path.join(DB_DIR, 'schema.sql')

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')


def get_db_connection():
    """Returns a connection to the SQLite database with Row factory and Foreign Keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """Initializes database tables using schema.sql and migrates new columns if necessary."""
    try:
        conn = get_db_connection()
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        
        cursor = conn.cursor()

        # Migrate sessions table
        cursor.execute("PRAGMA table_info(sessions)")
        sess_cols = [row['name'] for row in cursor.fetchall()]
        new_sess_cols = [
            ('audio_file_path', 'TEXT DEFAULT ""'),
            ('total_chunks', 'INTEGER DEFAULT 0'),
            ('avg_rms', 'REAL DEFAULT 0.0'),
            ('max_peak', 'REAL DEFAULT 0.0'),
            ('avg_confidence', 'REAL DEFAULT 0.0')
        ]
        for col_name, col_def in new_sess_cols:
            if col_name not in sess_cols:
                cursor.execute(f"ALTER TABLE sessions ADD COLUMN {col_name} {col_def}")

        # Migrate snore_events table
        cursor.execute("PRAGMA table_info(snore_events)")
        event_cols = [row['name'] for row in cursor.fetchall()]
        new_event_cols = [
            ('event_number', 'INTEGER DEFAULT 1'),
            ('confidence', 'REAL DEFAULT 0.0'),
            ('detection_method', 'TEXT DEFAULT "Signal-Processing Rule-Based v1"'),
            ('detection_reason', 'TEXT DEFAULT ""'),
            ('spectral_centroid', 'REAL DEFAULT 0.0'),
            ('spectral_bandwidth', 'REAL DEFAULT 0.0'),
            ('spectral_rolloff', 'REAL DEFAULT 0.0'),
            ('spectral_flatness', 'REAL DEFAULT 0.0'),
            ('zero_crossing_rate', 'REAL DEFAULT 0.0'),
            ('low_frequency_energy', 'REAL DEFAULT 0.0'),
            ('mid_frequency_energy', 'REAL DEFAULT 0.0'),
            ('high_frequency_energy', 'REAL DEFAULT 0.0'),
            ('crest_factor', 'REAL DEFAULT 0.0')
        ]
        for col_name, col_def in new_event_cols:
            if col_name not in event_cols:
                cursor.execute(f"ALTER TABLE snore_events ADD COLUMN {col_name} {col_def}")

        conn.commit()
        conn.close()
        logging.info("💾 [SQLITE DATABASE] Schema initialized & migrations applied successfully.")
    except Exception as err:
        logging.error(f"❌ [SQLITE INIT ERROR] Failed to initialize database: {err}")


def create_session():
    """Creates a new active monitoring session and returns its ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sessions (start_time, status)
            VALUES (?, 'active')
        """, (datetime.now().isoformat(),))
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        logging.info(f"💾 [SQLITE] New active session #{session_id} created.")
        return session_id
    except Exception as err:
        logging.error(f"❌ [SQLITE CREATE SESSION ERROR] {err}")
        return 1  # Fallback ID


def end_session(session_id, metrics=None):
    """Marks a session as completed and updates summary metrics in SQLite."""
    metrics = metrics or {}
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE sessions
            SET end_time = ?,
                duration_seconds = ?,
                total_chunks = ?,
                total_snores = ?,
                total_snore_duration = ?,
                avg_snore_duration = ?,
                longest_snore = ?,
                avg_intensity_db = ?,
                max_intensity_db = ?,
                avg_rms = ?,
                max_peak = ?,
                dominant_freq_hz = ?,
                snoring_percentage = ?,
                avg_confidence = ?,
                snore_score = ?,
                snore_personality = ?,
                survival_score = ?,
                funny_verdict = ?,
                audio_file_path = ?,
                status = 'completed'
            WHERE id = ?
        """, (
            datetime.now().isoformat(),
            metrics.get('duration_seconds', 0.0),
            metrics.get('total_chunks', 0),
            metrics.get('total_snores', 0),
            metrics.get('total_snore_duration', 0.0),
            metrics.get('avg_snore_duration', 0.0),
            metrics.get('longest_snore', 0.0),
            metrics.get('avg_intensity_db', -80.0),
            metrics.get('max_intensity_db', -80.0),
            metrics.get('avg_rms', 0.0),
            metrics.get('max_peak', 0.0),
            metrics.get('dominant_freq_hz', 0.0),
            metrics.get('snoring_percentage', 0.0),
            metrics.get('avg_confidence', 0.0),
            metrics.get('snore_score', 0.0),
            metrics.get('snore_personality', 'Gentle Purrer'),
            metrics.get('survival_score', 100.0),
            metrics.get('funny_verdict', 'Normal ambient sleeper'),
            metrics.get('audio_file_path', ''),
            int(session_id)
        ))
        conn.commit()
        conn.close()
        logging.info(f"💾 [SQLITE] Session #{session_id} marked completed with total_snores={metrics.get('total_snores', 0)}.")
    except Exception as err:
        logging.error(f"❌ [SQLITE END SESSION ERROR] Failed to update session #{session_id}: {err}")


def record_snore_event(session_id, event_data):
    """Records a single detected snore event with complete spectral features for a given session."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO snore_events (
                session_id, event_number, start_time, end_time, duration_seconds,
                intensity_db, peak_amplitude, rms_energy, dominant_freq_hz,
                confidence, detection_method, detection_reason,
                spectral_centroid, spectral_bandwidth, spectral_rolloff,
                spectral_flatness, zero_crossing_rate,
                low_frequency_energy, mid_frequency_energy, high_frequency_energy,
                crest_factor, time_since_prev_snore, audio_clip_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            int(session_id),
            int(event_data.get('event_number', event_data.get('id', 1))),
            event_data.get('start_time', datetime.now().strftime('%H:%M:%S')),
            event_data.get('end_time', datetime.now().strftime('%H:%M:%S')),
            float(event_data.get('duration_seconds', 0.0)),
            float(event_data.get('intensity_db', 0.0)),
            float(event_data.get('peak_amplitude', 0.0)),
            float(event_data.get('rms_energy', 0.0)),
            float(event_data.get('dominant_freq_hz', 0.0)),
            float(event_data.get('confidence', 0.0)),
            str(event_data.get('detection_method', 'Signal-Processing Rule-Based v1')),
            str(event_data.get('detection_reason', '')),
            float(event_data.get('spectral_centroid', 0.0)),
            float(event_data.get('spectral_bandwidth', 0.0)),
            float(event_data.get('spectral_rolloff', 0.0)),
            float(event_data.get('spectral_flatness', 0.0)),
            float(event_data.get('zero_crossing_rate', 0.0)),
            float(event_data.get('low_frequency_energy', 0.0)),
            float(event_data.get('mid_frequency_energy', 0.0)),
            float(event_data.get('high_frequency_energy', 0.0)),
            float(event_data.get('crest_factor', 0.0)),
            float(event_data.get('time_since_prev_snore', 0.0)),
            str(event_data.get('audio_clip_path', ''))
        ))
        event_id = cursor.lastrowid
        conn.commit()
        conn.close()
        logging.info(f"💾 [SQLITE] Snore Event #{event_data.get('event_number', 1)} for Session #{session_id} saved (DB Row #{event_id}).")
        return event_id
    except Exception as err:
        logging.error(f"❌ [SQLITE RECORD EVENT ERROR] Failed to record event for session #{session_id}: {err}")
        return None


def get_session(session_id):
    """Retrieves a single session record by ID."""
    try:
        conn = get_db_connection()
        session = conn.execute("SELECT * FROM sessions WHERE id = ?", (int(session_id),)).fetchone()
        conn.close()
        return dict(session) if session else None
    except Exception as err:
        logging.error(f"❌ [SQLITE GET SESSION ERROR] {err}")
        return None


def get_all_sessions():
    """Retrieves all past monitoring sessions ordered by start time descending."""
    try:
        conn = get_db_connection()
        sessions = conn.execute("SELECT * FROM sessions ORDER BY start_time DESC").fetchall()
        conn.close()
        return [dict(s) for s in sessions]
    except Exception as err:
        logging.error(f"❌ [SQLITE GET ALL SESSIONS ERROR] {err}")
        return []


def get_session_events(session_id):
    """Retrieves all snore events recorded for a session ordered by event_number / start_time."""
    try:
        conn = get_db_connection()
        events = conn.execute(
            "SELECT * FROM snore_events WHERE session_id = ? ORDER BY event_number ASC, start_time ASC",
            (int(session_id),)
        ).fetchall()
        conn.close()
        return [dict(e) for e in events]
    except Exception as err:
        logging.error(f"❌ [SQLITE GET SESSION EVENTS ERROR] {err}")
        return []
