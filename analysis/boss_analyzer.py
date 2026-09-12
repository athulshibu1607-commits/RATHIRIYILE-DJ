"""
SNORESCAN Phase 13 — Boss Analyzer & Entertainment Engine.

Calculates deterministic Snore Boss attributes, Snore Court verdicts,
Guess The Snore trivia events, and Hall of Shame leaderboards from session audio statistics.
"""

import math
import hashlib
from database import get_all_sessions, get_session_events, get_session


class BossAnalyzer:
    """Generates deterministic Snore Boss statistics and battle parameters."""

    BOSS_NAMES = [
        "THE SNORE DEMON",
        "THE HUMAN TRACTOR",
        "THE SLEEPING VOLCANO",
        "THE NIGHTMARE ENGINE",
        "THE SLEEP BEAST",
        "THE FINAL SNORE"
    ]

    COURT_VERDICTS = {
        "ME": [
            "GUILTY AS CHARGED! The defendant admits to acoustic terrorism under the duvet.",
            "VERDICT: Sentence set to 1,000 extra pillows and a mandatory nasal strip."
        ],
        "MY ROOMMATE": [
            "FALSE ACCUSATION! The roommate was innocent; your throat produced the 85dB sonic boom.",
            "VERDICT: You owe your roommate breakfast for the rest of the week."
        ],
        "THE DOG": [
            "CANINE EXONERATED! Fido was fast asleep without a single bark.",
            "VERDICT: The dog gets extra belly rubs; you get sleep therapy."
        ],
        "A GHOST": [
            "PARANORMAL INVESTIGATION COMPLETE! The ectoplasm test returned 0%. It was you.",
            "VERDICT: The ghost left the building due to noise complaints."
        ],
        "ALIENS": [
            "UNIDENTIFIED FLYING SNORE! NASA confirmed no alien signals; all noise originated from your uvula.",
            "VERDICT: Abduction request denied due to excessive decibels."
        ],
        "UNKNOWN ENTITY": [
            "MYSTERY SOLVED! The unknown entity is your snoring alter-ego.",
            "VERDICT: Case closed. Defendant ordered to wear earplugs."
        ]
    }

    def generate_boss(self, session_id: int, session: dict, stats: dict, events: list) -> dict:
        """
        Generates deterministic boss data based on real session audio metrics.
        
        Zero-event sessions produce a low-level sleeping minion safely.
        """
        snores = stats.get('total_snores', 0)
        max_intensity = stats.get('max_intensity_db', -60.0)
        duration = stats.get('total_snore_duration', 0.0)
        dominant_freq = stats.get('dominant_freq_hz', 150.0)

        # Deterministic seed from session_id
        seed_str = f"boss_{session_id}_{snores}_{int(abs(max_intensity))}"
        hash_val = int(hashlib.md5(seed_str.encode('utf-8')).hexdigest(), 16)

        # Boss selection
        boss_idx = hash_val % len(self.BOSS_NAMES)
        name = self.BOSS_NAMES[boss_idx]

        # Calculate Boss Level (1 to 99)
        level = min(99, max(1, int(snores * 1.5 + (max_intensity + 60) * 0.5)))
        if snores == 0:
            level = 1
            name = "SLEEPING MINION (TIRED)"

        # Max HP based on total snores and intensity
        max_hp = max(20, min(1000, int(100 + snores * 12 + abs(max_intensity) * 2)))
        hp = max_hp  # Initial battle state

        # Attack Power & Chaos Index
        attack_power = min(999, max(10, int(abs(max_intensity) * 2.5 + duration * 0.5)))
        chaos = min(100, max(5, int(snores * 3 + (300 - dominant_freq) * 0.1)))

        # Boss Special Attack
        special_moves = [
            "SONIC UVULA BLAST",
            "BEDFRAME SHAKE",
            "WINDOW RATTLE IMPACT",
            "DECIBEL CRUSH",
            "REM SLEEP DEMOLITION"
        ]
        special_move = special_moves[hash_val % len(special_moves)]

        # Boss power score (entertainment metric)
        boss_power = int(snores * 8 + abs(max_intensity) * 1.5 + level * 5)

        return {
            'session_id': session_id,
            'name': name,
            'level': level,
            'hp': hp,
            'max_hp': max_hp,
            'attack_power': attack_power,
            'chaos': chaos,
            'boss_power': boss_power,
            'snores': snores,
            'special_move': special_move,
            'is_sleeping': (snores == 0)
        }

    def get_snore_court_verdict(self, culprit: str) -> dict:
        """Returns deterministic Snore Court verdict for chosen culprit."""
        culprit_upper = culprit.upper()
        verdict_pair = self.COURT_VERDICTS.get(
            culprit_upper,
            self.COURT_VERDICTS["UNKNOWN ENTITY"]
        )
        return {
            'culprit': culprit,
            'verdict': verdict_pair[0],
            'sentence': verdict_pair[1]
        }

    def get_guess_the_snore_trivia(self, session_id: int, events: list) -> dict:
        """
        Prepares a Trivia question using real detected session audio events.
        If no events exist, provides a safe fallback trivia question.
        """
        if not events:
            return {
                'has_events': False,
                'event_index': 0,
                'duration': 0.0,
                'intensity_db': -60.0,
                'dominant_freq_hz': 0.0,
                'question': "Zero snore events detected in this session. What was the ambient noise level?",
                'options': [
                    {"label": "😴 PIN-DROP SILENCE", "correct": True},
                    {"label": "🐷 SUBTLE SNORE", "correct": False},
                    {"label": "🚗 TRAFFIC NOISE", "correct": False},
                    {"label": "👽 ALIEN WHISPER", "correct": False}
                ],
                'explanation': "The room was completely quiet with 0 decibel spikes!"
            }

        # Select primary event (e.g. longest or strongest)
        selected = max(events, key=lambda e: e.get('intensity_db', -100.0))
        dur = selected.get('duration_seconds', 1.0)
        intensity = selected.get('intensity_db', -30.0)
        freq = selected.get('dominant_freq_hz', 150.0)

        # Build options with 1 correct snore option and 3 decoys
        options = [
            {"label": "🐷 REAL SNORE BURST", "correct": True},
            {"label": "😴 NORMAL BREATHING", "correct": False},
            {"label": "🚗 REVVED MOTORCYCLE ENGINE", "correct": False},
            {"label": "👽 UNKNOWN CREATURE SCREAM", "correct": False}
        ]

        return {
            'has_events': True,
            'event_index': selected.get('event_index', 1),
            'duration': round(dur, 2),
            'intensity_db': round(intensity, 1),
            'dominant_freq_hz': round(freq, 1),
            'question': f"Audio Burst #{selected.get('event_index', 1)} lasted {round(dur, 2)}s at {round(intensity, 1)} dB ({round(freq, 1)} Hz). What was this sound?",
            'options': options,
            'explanation': f"Correct! It was a real detected snore event with a frequency peak at {round(freq, 1)} Hz!"
        }

    def get_hall_of_shame(self) -> dict:
        """Generates Hall of Shame leaderboards using real SQLite session records."""
        raw_sessions = get_all_sessions()
        if not raw_sessions:
            return {
                'most_snores': None,
                'loudest': None,
                'longest': None,
                'most_chaotic': None
            }

        # Enrich session metrics
        enriched = []
        for s in raw_sessions:
            events = get_session_events(s['id'])
            total_snores = s.get('total_snores', 0)
            max_intensity = s.get('max_intensity_db', -99.0)
            total_dur = s.get('total_snore_duration', 0.0)
            chaos = min(100, int(total_snores * 4 + abs(max_intensity) * 0.5))

            enriched.append({
                'id': s['id'],
                'start_time': s.get('start_time', 'N/A'),
                'total_snores': total_snores,
                'max_intensity_db': max_intensity,
                'total_snore_duration': total_dur,
                'chaos': chaos
            })

        most_snores = max(enriched, key=lambda s: s['total_snores'])
        loudest = max(enriched, key=lambda s: s['max_intensity_db'])
        longest = max(enriched, key=lambda s: s['total_snore_duration'])
        most_chaotic = max(enriched, key=lambda s: s['chaos'])

        return {
            'most_snores': most_snores,
            'loudest': loudest,
            'longest': longest,
            'most_chaotic': most_chaotic
        }
