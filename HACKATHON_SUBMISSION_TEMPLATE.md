<img width="1280" height="640" alt="git (1)" src="https://github.com/user-attachments/assets/8920b256-2ba8-4988-b824-5351134eb4bd" />

# SNORESCAN 😴🔊

## Basic Details
### Team Name: SnoozeSquad

### Team Members
- Team Lead: Athul - College
- Member 2: [Name] - [College]
- Member 3: [Name] - [College]

### Project Description
SNORESCAN is a continuous snoring detection, acoustic analysis, and roommate survival calculator application. It captures real-time microphone audio from your laptop, measures RMS energy and decibel loudness (dBFS), stores session history in SQLite, and generates hilarious post-session reports featuring custom snoring personalities.

### The Problem (that doesn't exist)
Roommates never admit to snoring, and until now, there has been no official acoustic decibel rating system to objectively prove that your bed partner sounds like a 1982 diesel tractor engine at 3:00 AM.

### The Solution (that nobody asked for)
Continuously stream ambient laptop microphone audio locally, compute real-time RMS energy and peak decibels, log WAV recordings, calculate Roommate Survival Scores, and award absurd hackathon personality badges (e.g. *Darth Vader*, *The Foghorn*, *Vintage Tractor*).

---

## Technical Details

### Technologies/Components Used
For Software:
- **Languages**: Python 3, HTML5, CSS3, JavaScript (ES6+)
- **Frameworks**: Flask 3.x
- **Signal & Audio Analysis**: NumPy, SciPy, Librosa, SoundFile, SoundDevice
- **Database**: SQLite 3
- **Machine Learning**: Scikit-Learn (classifier module)
- **UI Design System**: Vanilla CSS Dark Mode Glassmorphism

For Hardware:
- Laptop Microphone Input Hardware (No external hardware/Arduino required)

---

## Implementation

### Installation
```bash
cd useless_project_temp
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Run
```bash
python app.py
```
Open [http://127.0.0.1:5000/](http://127.0.0.1:5000/) in your browser.

---

## Important Medical Disclaimer
> [!IMPORTANT]
> SNORESCAN is created exclusively for entertainment, personal curiosity, and useless hackathon demonstration purposes. It **NEVER** provides medical diagnoses, clinical assessments, or healthcare advice. All output metrics consist solely of non-medical pattern indicators and screening observations.

---

Made with ❤️ at TinkerHub Useless Projects 

![Static Badge](https://img.shields.io/badge/TinkerHub-24?color=%23000000&link=https%3A%2F%2Fwww.tinkerhub.org%2F)
![Static Badge](https://img.shields.io/badge/UselessProjects--26-26?link=https%3A%2F%2Ftinkerhub.org%2Fevents%2F1M8ORET9A1%2Fuseless-projects-3.0)
