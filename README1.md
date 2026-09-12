<img width="1280" height="640" alt="git (1)" src="https://github.com/user-attachments/assets/8920b256-2ba8-4988-b824-5351134eb4bd" />



# SNORESCAN 😴🔊 🎯


## Basic Details
### Team Name: SnoozeSquad


### Team Members
- Team Lead: Athul Shibu Peethambaram - Providence College of Engineering, Chengannur
- Member 2: Akshaya Krishna - Providence College of Engineering, Chengannur

### Project Description
SNORESCAN is a desktop web application that continuously monitors bedroom acoustics through your laptop microphone, detects potential snoring events in real-time using FFT spectral analysis, stores comprehensive session telemetry in SQLite, and generates visually stunning acoustic reports accompanied by deterministic — and gloriously useless — hackathon entertainment statistics like Snore Personalities, Boss Battles, Roommate Damage Scores, and Snore Weather Forecasts.

### The Problem (that doesn't exist)
Roommates never admit to snoring, and until now, there has been no official acoustic decibel rating system to objectively prove that your bed partner sounds like a 1982 diesel tractor engine at 3:00 AM. Nobody has ever urgently needed to know their Snore Power Level, their Snore Personality archetype, or whether tonight's Snore Weather forecast predicts a Thunderstorm. Yet here we are.

### The Solution (that nobody asked for)
Continuously stream ambient laptop microphone audio locally, compute real-time RMS energy, peak amplitude, dBFS loudness, dominant frequency, and full FFT spectral analysis — then log every snoring event to SQLite, calculate Roommate Survival Scores, generate interactive Sleep Boss Battles, award absurd Snore Achievement badges (e.g. *Darth Vader*, *The Foghorn*, *Vintage Tractor*), predict fictional Snore Weather, and issue official SNORESCAN Institute™ certificates proving you are professionally annoying while unconscious. The app even features an immersive Day/Night world with orbital Sun & Moon animations that transform the background when you begin monitoring.

## Technical Details
### Technologies/Components Used
For Software:
- **Languages**: Python 3, HTML5, CSS3, JavaScript (ES6+)
- **Frameworks**: Flask 3.x
- **Libraries**: NumPy, SciPy, Librosa, SoundFile, SoundDevice, Scikit-Learn, Chart.js
- **Tools**: SQLite 3, Python unittest, Git, VS Code

For Hardware:
- Built-in Laptop Microphone Input (No external hardware / No Arduino required)
- Any standard PC or Mac with a working microphone
- No special specifications needed — runs on commodity hardware

### Implementation
For Software:
# Installation
```bash
# 1. Clone or navigate to project directory
cd "SNORE SCAN"

# 2. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate        # Windows
# source venv/bin/activate     # macOS/Linux

# 3. Install required dependencies
pip install -r requirements.txt
```

# Run
```bash
# Start the Flask web server
python app.py
```
Open your browser and navigate to: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

### Project Documentation
For Software:

# Screenshots (Add at least 3)
![Screenshot1](Add screenshot 1 here with proper name)
*SNORESCAN Home Dashboard — Day Mode with orbital Sun animation, glassmorphism hero section, and quick-action buttons for Start Monitoring, Demo Mode, and History.*

![Screenshot2](Add screenshot 2 here with proper name)
*Real-Time Monitoring — Night Mode with live waveform visualization, dBFS meter, detected snore event cards, and moonlit background with animated stars.*

![Screenshot3](Add screenshot 3 here with proper name)
*Session Report — Full acoustic analysis with frequency spectrum graph, timeline heatmap, Snore Personality card, Boss Battle arena, Roommate Damage Estimator, Snore Weather, and Achievements section.*

# Diagrams
![Workflow](Add your workflow/architecture diagram here)
*SNORESCAN Architecture: Laptop Microphone → Audio Capture (PCM 44.1kHz) → Signal Processing Pipeline (RMS / Peak / dBFS / FFT Spectrum) → Rule-Based Snore Detection Engine → SQLite Database Storage (Sessions & Events) → Pattern & Fun Intelligence Engine → Interactive Web Dashboard & Session Report.*

For Hardware:

# Schematic & Circuit
No external circuit required — SNORESCAN uses the laptop's built-in microphone directly via the SoundDevice library.

# Build Photos
No external hardware build — this is a pure software project running entirely on standard laptop hardware.

### Project Demo
# Video
[Add your demo video link here]
*Full walkthrough demonstrating: Day/Night world transition, real-time snore detection with live waveform, session report with acoustic graphs, Useless Intelligence™ features (Snore Personality, Boss Battle, Roommate Damage, Weather Forecast, Achievements), Demo Mode, and multi-session history comparison.*

# Additional Demos
[Add any extra demo materials/links]

## Team Contributions
- Athul Shibu Peethambaram: Full-stack development — Flask backend, audio processing pipeline, snore detection engine, SQLite database design, frontend UI/UX, Day/Night world engine, Useless Intelligence™ features, testing suite
- Akshaya Krishna: Project ideation, concept design, and presentation slides

---
Made with ❤️ at TinkerHub Useless Projects 

![Static Badge](https://img.shields.io/badge/TinkerHub-24?color=%23000000&link=https%3A%2F%2Fwww.tinkerhub.org%2F)
![Static Badge](https://img.shields.io/badge/UselessProjects--26-26?link=https%3A%2F%2Ftinkerhub.org%2Fevents%2F1M8ORET9A1%2Fuseless-projects-3.0)



