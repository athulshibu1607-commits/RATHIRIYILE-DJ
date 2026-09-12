# SNORESCAN

> Continuous local microphone snoring detection, spectral acoustic analysis, and ridiculous hackathon intelligence.

## What is SNORESCAN?
SNORESCAN is a desktop web application that continuously monitors bedroom acoustics through your laptop microphone, detects potential snoring events in real-time, stores comprehensive event telemetry in SQLite, and generates visually impressive acoustic reports accompanied by deterministic, useless hackathon entertainment statistics.

---

## Features
- 🎙️ **Real-Time Microphone Streaming**: Continuous 44.1 kHz PCM audio capture directly from local hardware (No cloud services / No Arduino required).
- 📊 **Spectral Acoustic Analysis**: Real-time extraction of RMS energy, peak amplitude, dBFS loudness, dominant frequency, spectral centroid, spectral bandwidth, spectral rolloff, and spectral flatness.
- 🗄️ **SQLite Persistence**: Complete single-source-of-truth storage for sessions and detected event telemetry.
- 📈 **Visual Graphs & Timeline**: Reconstructive timeline bar, segment activity heatmaps, frequency spectrum graphs, and multi-session trend charts.
- ⚔️ **SNORESCAN USELESS INTELLIGENCE™**:
  - **Snore Personality 2.0**: 10 deterministic signatures (Jet Engine Mode, Nuclear Alarm Clock, Boss Fight Mode, Tractor Mode, Gentle Kitten Purr, etc.).
  - **Snore Power Level**: 0–100 score & intensity level classification.
  - **Roommate Damage Estimator**: Calculates remaining roommate patience %.
  - **Sleep Boss Battle**: Gamified boss fight encounters with custom special moves.
  - **Snore Weather & Forecast**: Fictional weather system with "Snore Degrees".
  - **Sleep DJ / Music Genre**: Music genre assignment based on dominant frequencies.
  - **Snore Achievements**: Badge unlock system derived from real statistics.
  - **Official Certificate**: Printable/downloadable SNORESCAN Institute certificate.
- 🔮 **Demo Mode**: Isolated, instant demonstration mode for presentation without microphone input.
- 🏆 **Multi-Session Comparison & History**: Compare multiple sessions side-by-side with historical Snore Battles and CSV data export.

---

## Technology Stack
- **Backend Framework**: Python 3 / Flask
- **Audio & Signal Processing**: SoundDevice, NumPy, SciPy, Librosa, SoundFile
- **Database**: SQLite3
- **Frontend UI**: Modern HTML5, Vanilla CSS3 (Dark Glassmorphism UI), Vanilla JavaScript, Chart.js

---

## How It Works
```
Laptop Microphone 
   └─► Audio Stream Capture (PCM 44.1kHz)
         └─► Signal Processing Pipeline (RMS / Peak / dBFS / FFT Spectrum)
               └─► Rule-Based Snore Detection Engine
                     └─► SQLite Database Storage (Sessions & Events)
                           └─► Pattern & Fun Intelligence Engine
                                 └─► Interactive Web Dashboard & Session Report
```

---

## Installation

```bash
# 1. Clone or navigate to project repository
cd "d:\SNORE SCAN"

# 2. Activate virtual environment
.\venv\Scripts\activate

# 3. Install required dependencies
pip install -r requirements.txt
```

---

## Running SNORESCAN

```bash
# Start Flask Web Server
python app.py
```
Open your browser and navigate to: `http://127.0.0.1:5000`

---

## Usage Walkthrough

1. **Start Application**: Open `http://127.0.0.1:5000`.
2. **Open Monitoring**: Click **START MONITORING** or navigate to `/monitoring`.
3. **Capture Audio**: Produce vocal or snoring-like acoustic sounds. Real-time waveforms, metrics, and detected event cards will update dynamically.
4. **Stop Monitoring**: Click **STOP MONITORING** to finalize session metrics and save to SQLite.
5. **View Report**: Explore comprehensive session graphs, timeline, pattern analysis, and SNORESCAN Useless Intelligence™.
6. **Multi-Session History**: Navigate to `/history` to compare past sessions or export event data as CSV.

---

## Demo Mode
Click **START DEMO MODE** from the home page or navigate to `/demo`.
- Demo Mode runs using isolated, deterministic fictional data.
- It allows presenters to showcase the live dashboard, event cards, interactive graphs, and report features without needing a live microphone.
- Demo data is **NEVER** saved to the real SQLite database and is excluded from Hall of Fame records and streaks.

---

## Why is this useful? (Hackathon Presentation)

### "Why does this software even exist?"
**Short Answer**: It probably shouldn't.

**Technical Reality**:
While the entertainment metrics make audiences laugh, SNORESCAN demonstrates an end-to-end real-time acoustic processing architecture:
- Low-latency real-time PCM audio streaming & buffer management.
- Multi-dimensional spectral signal processing (FFT, centroids, bandwidths, rolloffs).
- Robust relational database schema design with full transaction isolation.
- Interactive multi-session analytics, temporal gap clustering, and historical trend tracking.

---

## Medical Disclaimer

> **IMPORTANT NOTICE**: SNORESCAN is built exclusively for personal curiosity, entertainment, and hackathon demonstration. It **NEVER** provides medical diagnosis, medical advice, sleep apnea evaluation, or clinical assessment. All output metrics are fictional or non-medical screening observations.
