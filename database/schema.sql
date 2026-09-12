-- SNORESCAN SQLite Database Schema

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    duration_seconds REAL DEFAULT 0.0,
    total_chunks INTEGER DEFAULT 0,
    total_snores INTEGER DEFAULT 0,
    total_snore_duration REAL DEFAULT 0.0,
    avg_snore_duration REAL DEFAULT 0.0,
    longest_snore REAL DEFAULT 0.0,
    avg_intensity_db REAL DEFAULT -80.0,
    max_intensity_db REAL DEFAULT -80.0,
    avg_rms REAL DEFAULT 0.0,
    max_peak REAL DEFAULT 0.0,
    dominant_freq_hz REAL DEFAULT 0.0,
    snoring_percentage REAL DEFAULT 0.0,
    avg_confidence REAL DEFAULT 0.0,
    snore_score REAL DEFAULT 0.0,
    snore_personality TEXT DEFAULT 'Pending Analysis',
    survival_score REAL DEFAULT 100.0,
    funny_verdict TEXT DEFAULT 'Session initialized.',
    audio_file_path TEXT DEFAULT '',
    status TEXT CHECK(status IN ('active', 'completed', 'cancelled')) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS snore_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    event_number INTEGER DEFAULT 1,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_seconds REAL DEFAULT 0.0,
    intensity_db REAL DEFAULT 0.0,
    peak_amplitude REAL DEFAULT 0.0,
    rms_energy REAL DEFAULT 0.0,
    dominant_freq_hz REAL DEFAULT 0.0,
    confidence REAL DEFAULT 0.0,
    detection_method TEXT DEFAULT 'Signal-Processing Rule-Based v1',
    detection_reason TEXT DEFAULT '',
    spectral_centroid REAL DEFAULT 0.0,
    spectral_bandwidth REAL DEFAULT 0.0,
    spectral_rolloff REAL DEFAULT 0.0,
    spectral_flatness REAL DEFAULT 0.0,
    zero_crossing_rate REAL DEFAULT 0.0,
    low_frequency_energy REAL DEFAULT 0.0,
    mid_frequency_energy REAL DEFAULT 0.0,
    high_frequency_energy REAL DEFAULT 0.0,
    crest_factor REAL DEFAULT 0.0,
    time_since_prev_snore REAL DEFAULT 0.0,
    audio_clip_path TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_snore_events_session_id ON snore_events(session_id);
