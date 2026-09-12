"""
Phase 11 — SNORESCAN Fun, Useless & Hackathon Feature Engine
Calculates 100% deterministic entertainment metrics from real SQLite session audio statistics.
Guaranteed zero random values, zero machine learning, and 100% non-medical safety.
"""
import math
import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')

class FunAnalyzer:
    """
    Entertainment & Hackathon analysis engine for SNORESCAN.
    Produces funny, memorable, and deterministic metrics based exclusively on real acoustic session data.
    """

    PERSONALITIES_2_0 = [
        ("✈️ JET ENGINE MODE", "Your acoustic signature resembles a Boeing 747 preparing for takeoff.", "✈️"),
        ("🚨 NUCLEAR ALARM CLOCK", "Extremely loud, rapid acoustic blasts capable of waking entire neighborhoods.", "🚨"),
        ("👹 BOSS FIGHT MODE", "The final boss of sleep acoustic chaos.", "👹"),
        ("🌩️ THUNDER ENGINE", "Low-frequency acoustic thunder rumbles across the room.", "🌩️"),
        ("🚂 NIGHT EXPRESS", "Heavy freight train chugging through the midnight hour.", "🚂"),
        ("🏭 HEAVY MACHINERY MODE", "Continuous acoustic rumble demanding industrial-grade hearing protection.", "🏭"),
        ("🚜 TRACTOR MODE", "Your acoustic signature resembles a vintage tractor attempting to start at 3 AM.", "🚜"),
        ("🏍️ MOTORCYCLE MODE", "Steady, low-pitched acoustic idling.", "🏍️"),
        ("🐼 SLEEPY PANDA", "Occasional gentle snore bursts with calm, quiet intermissions.", "🐼"),
        ("🐱 GENTLE KITTEN PURR", "Soft, low-frequency rhythmic breathing with minimal rumble.", "🐱")
    ]

    def __init__(self, db_conn=None):
        self.db_conn = db_conn

    def get_snore_personality(self, stats: dict) -> dict:
        total_snores = stats.get('total_snores', stats.get('total_events', stats.get('events_in_session', 0)))
        snoring_pct = stats.get('snoring_percentage', stats.get('snore_percentage', 0.0))
        events_per_min = stats.get('events_per_minute', 0.0)
        avg_intensity = stats.get('avg_intensity_db', stats.get('avg_intensity', -80.0))
        max_intensity = stats.get('max_intensity_db', stats.get('max_intensity', avg_intensity))
        avg_freq = stats.get('dominant_freq_hz', stats.get('avg_dominant_frequency', 0.0))
        longest_snore = stats.get('longest_snore', stats.get('longest_event_duration', 0.0))

        if max_intensity > -15.0 and avg_freq > 300.0:
            name, desc, icon = self.PERSONALITIES_2_0[0]
        elif events_per_min > 10.0 and max_intensity > -20.0:
            name, desc, icon = self.PERSONALITIES_2_0[1]
        elif snoring_pct > 25.0 and longest_snore >= 3.0:
            name, desc, icon = self.PERSONALITIES_2_0[2]
        elif max_intensity > -18.0 and (0.0 < avg_freq < 220.0 or avg_freq == 0.0):
            name, desc, icon = self.PERSONALITIES_2_0[3]
        elif total_snores > 15 and (0.0 < avg_freq < 200.0 or avg_freq == 0.0):
            name, desc, icon = self.PERSONALITIES_2_0[4]
        elif events_per_min > 6.0 and max_intensity > -25.0:
            name, desc, icon = self.PERSONALITIES_2_0[5]
        elif events_per_min > 4.0 or longest_snore >= 2.0 or avg_intensity > 70.0:
            name, desc, icon = self.PERSONALITIES_2_0[6]
        elif events_per_min > 2.0:
            name, desc, icon = self.PERSONALITIES_2_0[7]
        elif total_snores >= 1:
            name, desc, icon = self.PERSONALITIES_2_0[8]
        else:
            name, desc, icon = self.PERSONALITIES_2_0[9]

        return {'name': name, 'explanation': desc, 'icon': icon}

    def calculate_snore_power(self, stats: dict) -> dict:
        total_snores = stats.get('total_snores', stats.get('total_events', stats.get('events_in_session', 0)))
        if total_snores == 0:
            return {
                'score': 0.0,
                'level': 'WHISPER',
                'level_name': 'WHISPER',
                'disclaimer': "Entertainment score based on recorded acoustic activity."
            }

        snoring_pct = stats.get('snoring_percentage', stats.get('snore_percentage', 0.0))
        events_per_min = stats.get('events_per_minute', 0.0)
        avg_int = stats.get('avg_intensity_db', stats.get('avg_intensity', -80.0))
        max_int = stats.get('max_intensity_db', stats.get('max_intensity', avg_int))

        # Handle DB intensity dBFS vs 0-100 score
        int_score = max_int if max_int > 0.0 else max(0.0, max_int + 80.0)

        power_score = min(100.0, max(0.0, (snoring_pct * 0.4) + (min(50.0, events_per_min * 5.0) * 0.3) + (int_score * 0.3)))
        power_score = round(power_score, 1)

        if power_score >= 81.0:
            level = "NUCLEAR"
        elif power_score >= 61.0:
            level = "DANGEROUSLY LOUD"
        elif power_score >= 41.0:
            level = "SERIOUS"
        elif power_score >= 21.0:
            level = "CASUAL"
        else:
            level = "WHISPER"

        return {
            'score': power_score,
            'level': level,
            'level_name': level,
            'disclaimer': "Entertainment score based on recorded acoustic activity."
        }

    def calculate_roommate_damage(self, stats: dict) -> dict:
        survival = stats.get('survival_score', None)
        if survival is None:
            snoring_pct = stats.get('snoring_percentage', stats.get('snore_percentage', 0.0))
            avg_int = stats.get('avg_intensity_db', stats.get('avg_intensity', 0.0))
            longest = stats.get('longest_snore', stats.get('longest_event_duration', 0.0))
            total_ev = stats.get('total_snores', stats.get('total_events', 0))
            
            damage_pts = (snoring_pct * 0.4) + (min(40.0, total_ev * 1.5)) + (min(30.0, longest * 3.0))
            patience = max(0.0, min(100.0, 100.0 - damage_pts))
        else:
            patience = float(survival)

        patience = round(patience, 1)

        if patience >= 90.0:
            desc = "Roommate probably sleeping peacefully."
        elif patience >= 70.0:
            desc = "Minor disturbance detected."
        elif patience >= 40.0:
            desc = "Roommate may be reconsidering the friendship."
        elif patience >= 20.0:
            desc = "Friendship stability critical."
        else:
            desc = "Emergency roommate evacuation recommended."

        return {
            'patience_remaining': patience,
            'patience_remaining_pct': patience,
            'description': desc,
            'disclaimer': "Entertainment only."
        }

    def calculate_boss_battle(self, stats: dict) -> dict:
        power_info = self.calculate_snore_power(stats)
        power_score = power_info['score']
        longest_snore = stats.get('longest_snore', stats.get('longest_event_duration', 0.0))

        if power_score >= 80.0:
            boss_level = "LEVEL 6 — FINAL BOSS: THE SNORE TITAN"
            boss_name = "THE SNORE TITAN"
        elif power_score >= 65.0:
            boss_level = "LEVEL 5 — NIGHTMARE ENGINE"
            boss_name = "NIGHTMARE ENGINE"
        elif power_score >= 50.0:
            boss_level = "LEVEL 4 — THUNDER MONSTER"
            boss_name = "THUNDER MONSTER"
        elif power_score >= 35.0:
            boss_level = "LEVEL 3 — TRACTOR BEAST"
            boss_name = "TRACTOR BEAST"
        elif power_score >= 15.0:
            boss_level = "LEVEL 2 — SNORE GOBLIN"
            boss_name = "SNORE GOBLIN"
        else:
            boss_level = "LEVEL 1 — SLEEPING POTATO"
            boss_name = "SLEEPING POTATO"

        special_move = f"{longest_snore:.1f} second continuous rumble" if longest_snore > 0 else "Silent Stealth Charge"

        return {
            'boss_level': boss_level,
            'boss_name': boss_name,
            'level': boss_level,
            'power': power_score,
            'special_move': special_move
        }

    def generate_session_title(self, stats: dict) -> str:
        power_score = self.calculate_snore_power(stats)['score']
        longest_snore = stats.get('longest_snore', stats.get('longest_event_duration', 0.0))
        snoring_pct = stats.get('snoring_percentage', stats.get('snore_percentage', 0.0))
        events_per_min = stats.get('events_per_minute', 0.0)
        survival = self.calculate_roommate_damage(stats)['patience_remaining']
        total_snores = stats.get('total_snores', stats.get('total_events', 0))

        if power_score >= 80.0:
            return "THE SNORE APOCALYPSE"
        elif longest_snore >= 3.0:
            return "THE 3 AM ENGINE STARTUP"
        elif snoring_pct >= 15.0:
            return "THE NIGHT OF THE TRACTOR"
        elif events_per_min >= 5.0:
            return "OPERATION: NOISY PILLOW"
        elif survival < 50.0:
            return "PROJECT: ROOMMATE SURVIVAL"
        elif total_snores >= 1:
            return "MISSION: SLEEP LOUDLY"
        else:
            return "THE PEACEFUL SILENCE"

    def calculate_snore_weather(self, stats: dict) -> dict:
        power_score = self.calculate_snore_power(stats)['score']
        events_per_min = stats.get('events_per_minute', 0.0)

        if power_score >= 85.0:
            weather_state = "CATEGORY 5 SNORE"
        elif power_score >= 70.0:
            weather_state = "THUNDERSTORM"
        elif power_score >= 50.0:
            weather_state = "STORM"
        elif power_score >= 30.0:
            weather_state = "WINDY"
        elif power_score >= 15.0:
            weather_state = "CLOUDY"
        else:
            weather_state = "CALM"

        return {
            'state': weather_state,
            'condition': weather_state,
            'temp': f"{int(power_score * 0.8 + 20)} SNORE DEGREES",
            'temperature': f"{int(power_score * 0.8 + 20)} SNORE DEGREES",
            'wind': f"{events_per_min:.1f} events/min",
            'storm_intensity': f"{int(power_score)}/100",
            'label': "100% useless fictional weather system."
        }

    def calculate_snore_forecast(self, stats: dict) -> dict:
        power_score = self.calculate_snore_power(stats)['score']
        forecast_prob = int(min(99, max(5, power_score * 0.9 + 10)))

        return {
            'tractor_chance_pct': forecast_prob,
            'probability': f"{forecast_prob}% chance of tractor activity.",
            'turbulence_prob': "High probability of midnight turbulence.",
            'engine_noises': "Expect scattered engine noises.",
            'advice': "High probability of midnight turbulence and scattered engine noises.",
            'disclaimer': "Entertainment prediction — not a real forecast."
        }

    def calculate_sleep_genre(self, stats: dict) -> dict:
        max_int = stats.get('max_intensity_db', stats.get('max_intensity', -80.0))
        avg_freq = stats.get('dominant_freq_hz', stats.get('avg_dominant_frequency', 0.0))
        power_score = self.calculate_snore_power(stats)['score']
        events_per_min = stats.get('events_per_minute', 0.0)
        total_snores = stats.get('total_snores', stats.get('total_events', 0))

        if (max_int > -18.0 or max_int > 70.0) and avg_freq > 300.0:
            name = "HEAVY METAL MODE"
            desc = "High-pitched, loud acoustic distortion fills the venue."
        elif 0.0 < avg_freq < 180.0 and power_score >= 50.0:
            name = "INDUSTRIAL MODE"
            desc = "Your bedroom has apparently become a factory."
        elif max_int > -25.0 or max_int > 60.0:
            name = "BASS BOOSTED MODE"
            desc = "Heavy low-end sub-bass frequencies rumbling."
        elif events_per_min > 5.0:
            name = "TECHNO BEDROOM"
            desc = "Fast BPM repetitive acoustic beat."
        elif total_snores > 0:
            name = "LOFI SLEEP MODE"
            desc = "Gentle ambient acoustic track."
        else:
            name = "LOFI SILENCE MODE"
            desc = "Zero BPM acoustic peace."

        return {'genre': name, 'description': desc}

    def generate_commentary(self, stats: dict, events: list = None) -> list:
        events = events or []
        if not events and stats.get('total_events', stats.get('total_snores', 0)) == 0:
            return [{"time": "00:00:00", "message": "🤫 The stadium has gone silent."}]

        commentary = []
        commentary.append({"time": "00:00:05", "message": "🎙️ AND WE HAVE CONTACT!"})

        max_int = stats.get('max_intensity_db', stats.get('max_intensity', -80.0))
        if max_int > -30.0 or max_int > 60.0:
            commentary.append({"time": "00:01:20", "message": "🚨 THAT ONE HAD SOME POWER!"})

        longest = stats.get('longest_snore', stats.get('longest_event_duration', 0.0))
        if longest >= 2.0:
            commentary.append({"time": "00:02:15", "message": "📢 THIS ONE IS STILL GOING..."})

        commentary.append({"time": "END", "message": "🏁 AND THAT'S THE END OF THE SNOREFEST!"})
        return commentary

    def calculate_combos(self, events: list) -> dict:
        max_combo = self._calculate_max_combo(events)
        return {
            'max_combo': max_combo,
            'max_combo_str': f"{max_combo}x" if max_combo > 0 else "0x",
            'banner': f"🔥 {max_combo} EVENT COMBO! Your sleep entered arcade mode." if max_combo >= 2 else "No combo"
        }

    def generate_report_card(self, stats: dict) -> dict:
        power_score = self.calculate_snore_power(stats)['score']
        card = self._calculate_report_card(stats, power_score)
        return {
            'loudness_grade': card['loudness'],
            'frequency_grade': card['frequency'],
            'chaos_grade': card['chaos'],
            'danger_grade': card['danger'],
            'roommate_danger': card['danger'],
            'engine_quality': card['engine_quality'],
            'uselessness_grade': card['overall_uselessness'],
            'overall_uselessness': card['overall_uselessness']
        }

    def generate_certificate(self, session_id, date_str: str, stats: dict) -> dict:
        total_snores = stats.get('total_snores', stats.get('total_events', 0))
        dur_min = stats.get('duration_minutes', round(float(stats.get('duration_seconds', 0.0)) / 60.0, 1))
        pers = self.get_snore_personality(stats)['name']
        power = self.calculate_snore_power(stats)['score']

        return {
            'title': "OFFICIAL SNORESCAN CERTIFICATE",
            'session_id': session_id,
            'date': date_str,
            'event_count': total_snores,
            'duration_minutes': dur_min,
            'personality': pers,
            'power_score': power,
            'institute': "Certified by the completely unnecessary SNORESCAN Institute."
        }

    def generate_share_card_data(self, session_id, stats: dict) -> dict:
        total_snores = stats.get('total_snores', stats.get('total_events', 0))
        snoring_pct = stats.get('snoring_percentage', stats.get('snore_percentage', 0.0))
        pers = self.get_snore_personality(stats)['name']
        power = self.calculate_snore_power(stats)['score']
        survival = self.calculate_roommate_damage(stats)['patience_remaining']
        title = self.generate_session_title(stats)

        return {
            'title': title,
            'session_id': session_id,
            'personality': pers,
            'power': power,
            'events': total_snores,
            'snoring_pct': snoring_pct,
            'roommate_survival': survival,
            'top_achievement': "🏆 TRACTOR STARTED" if total_snores > 0 else "🕊️ PEACEFUL SLEEPER"
        }

    def check_achievements(self, stats: dict, events: list = None, max_combo: int = 1) -> list:
        events = events or []
        ach_list = self._calculate_achievements(stats, events, max_combo)
        result = []
        for a in ach_list:
            result.append({
                'title': a['title'],
                'desc': a['desc'],
                'icon': a['icon'],
                'unlocked': True
            })
        return result

    def get_snore_streak(self) -> dict:
        from database.db import get_all_sessions
        sessions = get_all_sessions()
        if not sessions:
            return {'current_streak': 0, 'longest_streak': 0, 'current_streak_str': 'No streak yet.', 'status': 'No streak yet.'}

        chrono_sessions = sorted(sessions, key=lambda s: str(s.get('start_time', '')))
        current_streak = 0
        longest_streak = 0

        for s in chrono_sessions:
            if (s.get('total_snores', 0) or 0) > 0:
                current_streak += 1
                if current_streak > longest_streak:
                    longest_streak = current_streak
            else:
                current_streak = 0

        status_str = f"🔥 {current_streak} SESSION SNORE STREAK" if current_streak > 0 else "No streak yet."
        return {
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'current_streak_str': status_str,
            'status': status_str
        }

    def calculate_snore_streak(self) -> dict:
        return self.get_snore_streak()

    def get_hall_of_fame(self) -> dict:
        wr = self.get_world_records()
        records = wr.get('records', [])
        
        hof = {
            'loudest_event': {'session_id': 'N/A', 'value': 'N/A'},
            'longest_event': {'session_id': 'N/A', 'value': 'N/A'},
            'most_events_session': {'session_id': 'N/A', 'value': 'N/A'}
        }

        for r in records:
            cat = r.get('category', '')
            if cat == 'LOUDEST EVENT':
                hof['loudest_event'] = {'session_id': r['session_id'], 'value': r['value']}
            elif cat == 'LONGEST EVENT':
                hof['longest_event'] = {'session_id': r['session_id'], 'value': r['value']}
            elif cat == 'MOST EVENTS IN SESSION':
                hof['most_events_session'] = {'session_id': r['session_id'], 'value': r['value']}

        return hof

    def get_world_records(self) -> dict:
        res = self.get_hall_of_fame_and_world_records()
        return {
            'records': res.get('records', []),
            'disclaimer': "Records from this SNORESCAN installation only."
        }

    def battle_sessions(self, session_id_a, session_id_b) -> dict:
        from database.db import get_session, get_session_events
        sa = get_session(session_id_a) or {}
        sb = get_session(session_id_b) or {}

        ea = get_session_events(session_id_a) if session_id_a else []
        eb = get_session_events(session_id_b) if session_id_b else []

        st_a = {
            'total_events': len(ea),
            'total_snores': len(ea),
            'snoring_percentage': float(dict(sa).get('snoring_percentage', 0.0) or 0.0),
            'avg_intensity': float(dict(sa).get('avg_intensity_db', -80.0) or -80.0),
            'max_intensity': float(dict(sa).get('max_intensity_db', -80.0) or -80.0),
            'longest_event_duration': float(dict(sa).get('longest_snore', 0.0) or 0.0)
        }
        st_b = {
            'total_events': len(eb),
            'total_snores': len(eb),
            'snoring_percentage': float(dict(sb).get('snoring_percentage', 0.0) or 0.0),
            'avg_intensity': float(dict(sb).get('avg_intensity_db', -80.0) or -80.0),
            'max_intensity': float(dict(sb).get('max_intensity_db', -80.0) or -80.0),
            'longest_event_duration': float(dict(sb).get('longest_snore', 0.0) or 0.0)
        }

        pw_a = self.calculate_snore_power(st_a)['score']
        pw_b = self.calculate_snore_power(st_b)['score']

        winner = session_id_a if pw_a >= pw_b else session_id_b
        return {
            'session_a': {'id': session_id_a, 'power': pw_a},
            'session_b': {'id': session_id_b, 'power': pw_b},
            'winner_session_id': winner,
            'summary': f"Session #{winner} achieved maximum acoustic chaos!"
        }

    def analyze_fun_features(self, session_id: int, session: dict, events: list, stats: dict) -> dict:
        total_snores = stats.get('total_snores', 0)
        snoring_pct = stats.get('snoring_percentage', 0.0)
        events_per_min = stats.get('events_per_minute', 0.0)
        avg_intensity = stats.get('avg_intensity_db', -80.0)
        max_intensity = stats.get('max_intensity_db', -80.0)
        avg_freq = stats.get('dominant_freq_hz', 0.0)
        longest_snore = stats.get('longest_snore', 0.0)

        pers_dict = self.get_snore_personality(stats)
        personality = pers_dict['name']
        pers_desc = pers_dict['explanation']

        snore_power = self.calculate_snore_power(stats)
        power_score = snore_power['score']
        roommate_damage = self.calculate_roommate_damage(stats)
        boss_battle = self.calculate_boss_battle(stats)

        max_combo = self._calculate_max_combo(events)
        combo_info = self.calculate_combos(events)
        commentary = self.generate_commentary(stats, events)
        session_title = self.generate_session_title(stats)
        snore_weather = self.calculate_snore_weather(stats)
        snore_forecast = self.calculate_snore_forecast(stats)
        sleep_genre = self.calculate_sleep_genre(stats)
        achievements = self.check_achievements(stats, events, max_combo)
        report_card = self.generate_report_card(stats)

        duration_min = round(float(session.get('duration_seconds', 0.0)) / 60.0, 1)
        certificate = self.generate_certificate(session_id, str(session.get('start_time', 'N/A'))[:10], stats)
        share_card = self.generate_share_card_data(session_id, stats)

        return {
            'session_id': session_id,
            'session_title': session_title,
            'personality_2_0': pers_dict,
            'snore_power': snore_power,
            'roommate_damage': roommate_damage,
            'boss_battle': boss_battle,
            'achievements': achievements,
            'snore_weather': snore_weather,
            'snore_forecast': snore_forecast,
            'sleep_genre': sleep_genre,
            'commentary': commentary,
            'combo_info': combo_info,
            'report_card': report_card,
            'certificate': certificate,
            'share_card': share_card
        }

    def _calculate_max_combo(self, events: list) -> int:
        if not events or len(events) < 2:
            return 1 if len(events) == 1 else 0

        max_combo = 1
        current_combo = 1

        for i in range(1, len(events)):
            prev_start = float(events[i-1].get('start_offset_sec', events[i-1].get('start_time', 0.0)))
            prev_dur = float(events[i-1].get('duration_seconds', events[i-1].get('duration', (events[i-1].get('end_time', prev_start + 2.0) - prev_start) if isinstance(events[i-1].get('end_time'), (int, float)) else 2.0)))
            prev_end = prev_start + prev_dur

            curr_start = float(events[i].get('start_offset_sec', events[i].get('start_time', prev_end + 10.0)))
            gap = curr_start - prev_end

            if gap <= 5.0:
                current_combo += 1
                if current_combo > max_combo:
                    max_combo = current_combo
            else:
                current_combo = 1

        return max_combo

    def _generate_commentary(self, events: list, stats: dict) -> list:
        return self.generate_commentary(stats, events)

    def _calculate_achievements(self, stats: dict, events: list, max_combo: int) -> list:
        total_snores = stats.get('total_snores', stats.get('total_events', 0))
        max_intensity = stats.get('max_intensity_db', stats.get('max_intensity', -80.0))
        longest_snore = stats.get('longest_snore', stats.get('longest_event_duration', 0.0))
        snoring_pct = stats.get('snoring_percentage', stats.get('snore_percentage', 0.0))
        min_freq = stats.get('min_dominant_freq_hz', stats.get('avg_dominant_frequency', 0.0))

        achievements = []
        if total_snores >= 1:
            achievements.append({'icon': '🏆', 'title': 'FIRST SNORE', 'desc': 'First detected acoustic snore event.'})
        if max_intensity > -30.0 or max_intensity > 60.0:
            achievements.append({'icon': '🔥', 'title': 'HOT ENGINE', 'desc': 'High acoustic intensity spike detected.'})
        if longest_snore >= 2.0:
            achievements.append({'icon': '🚜', 'title': 'TRACTOR STARTED', 'desc': 'Long continuous acoustic rumble recorded.'})
        if max_combo >= 2:
            achievements.append({'icon': '⚡', 'title': 'RAPID FIRE', 'desc': f'Achieved {max_combo}x rapid event combo.'})
        if max_intensity > -20.0 or max_intensity > 80.0:
            achievements.append({'icon': '🌋', 'title': 'VOLCANIC', 'desc': 'Peak amplitude reached maximum volume.'})
        if longest_snore >= 3.0:
            achievements.append({'icon': '🕰️', 'title': 'MARATHON SNORE', 'desc': 'Extended snore duration exceeded 3.0s.'})
        if 0.0 < min_freq < 150.0:
            achievements.append({'icon': '🌌', 'title': 'DEEP SPACE', 'desc': 'Low-frequency sub-bass resonance detected.'})
        if snoring_pct >= 20.0:
            achievements.append({'icon': '💀', 'title': 'ROOMMATE DESTROYER', 'desc': 'High snoring percentage across session.'})
        if total_snores >= 10:
            achievements.append({'icon': '🏅', 'title': '10 EVENTS', 'desc': 'Recorded 10+ snoring events in a single session.'})
        if total_snores >= 50:
            achievements.append({'icon': '🏅', 'title': '50 EVENTS', 'desc': 'Recorded 50+ snoring events in a single session.'})

        if not achievements:
            achievements.append({'icon': '🕊️', 'title': 'PEACEFUL SLEEPER', 'desc': 'Recorded 0 snoring events. Absolute silence.'})

        return achievements

    def _calculate_report_card(self, stats: dict, power_score: float) -> dict:
        max_int = stats.get('max_intensity_db', stats.get('max_intensity', -80.0))
        rate = stats.get('events_per_minute', 0.0)
        snoring_pct = stats.get('snoring_percentage', stats.get('snore_percentage', 0.0))
        survival = stats.get('survival_score', 100.0)

        if max_int > -15.0 or max_int > 80.0: grade_loud = "A+"
        elif max_int > -25.0 or max_int > 60.0: grade_loud = "A"
        elif max_int > -35.0 or max_int > 40.0: grade_loud = "B"
        elif max_int > -45.0 or max_int > 20.0: grade_loud = "C"
        else: grade_loud = "D"

        if rate > 8.0: grade_freq = "A+"
        elif rate > 5.0: grade_freq = "A"
        elif rate > 2.0: grade_freq = "B"
        elif rate > 0.5: grade_freq = "C"
        else: grade_freq = "F"

        if power_score > 75.0: grade_chaos = "S"
        elif power_score > 50.0: grade_chaos = "A"
        elif power_score > 25.0: grade_chaos = "B"
        else: grade_chaos = "C"

        if survival < 30.0: grade_danger = "SS"
        elif survival < 60.0: grade_danger = "S"
        elif survival < 85.0: grade_danger = "A"
        else: grade_danger = "F"

        if stats.get('longest_snore', stats.get('longest_event_duration', 0.0)) >= 3.0: grade_engine = "A+"
        elif stats.get('longest_snore', stats.get('longest_event_duration', 0.0)) >= 1.5: grade_engine = "A"
        else: grade_engine = "B"

        if power_score > 70.0: useless = "SSS"
        elif power_score > 30.0: useless = "SS"
        else: useless = "S"

        return {
            'loudness': grade_loud,
            'frequency': grade_freq,
            'chaos': grade_chaos,
            'danger': grade_danger,
            'engine_quality': grade_engine,
            'overall_uselessness': useless
        }

    def get_hall_of_fame_and_world_records(self) -> dict:
        from database.db import get_all_sessions, get_session_events
        sessions = get_all_sessions()
        if not sessions:
            return {
                'records_notice': "Records from this SNORESCAN installation only.",
                'records': []
            }

        analyzed = []
        all_events = []

        for s in sessions:
            events = get_session_events(s['id'])
            s_dur = float(s.get('duration_seconds', 0.0))
            snore_cnt = int(s.get('total_snores', 0) or 0)
            snore_dur = float(s.get('total_snore_duration', 0.0) or 0.0)
            pct = float(s.get('snoring_percentage', 0.0) or 0.0)
            max_int = float(s.get('max_intensity_db', -80.0) or -80.0)
            avg_int = float(s.get('avg_intensity_db', -80.0) or -80.0)
            longest = float(s.get('longest_snore', 0.0) or 0.0)
            rate = round((snore_cnt / s_dur * 60.0), 1) if s_dur > 0 else 0.0

            analyzed.append({
                'session_id': s['id'],
                'date': str(s.get('start_time', 'N/A'))[:10],
                'duration': s_dur,
                'total_snores': snore_cnt,
                'snoring_percentage': pct,
                'max_intensity': max_int,
                'avg_intensity': avg_int,
                'longest_snore': longest,
                'events_per_minute': rate
            })
            all_events.extend(events)

        records = []

        if all_events:
            loudest_ev = max(all_events, key=lambda e: float(e.get('intensity_db', -80.0)))
            records.append({
                'category': 'LOUDEST EVENT',
                'session_id': loudest_ev.get('session_id', 1),
                'value': f"{float(loudest_ev.get('intensity_db', -80.0)):.1f} dBFS"
            })

            longest_ev = max(all_events, key=lambda e: float(e.get('duration_seconds', 0.0)))
            records.append({
                'category': 'LONGEST EVENT',
                'session_id': longest_ev.get('session_id', 1),
                'value': f"{float(longest_ev.get('duration_seconds', 0.0)):.2f} sec"
            })

        if analyzed:
            most_ev_sess = max(analyzed, key=lambda s: s['total_snores'])
            records.append({
                'category': 'MOST EVENTS IN SESSION',
                'session_id': most_ev_sess['session_id'],
                'value': f"{most_ev_sess['total_snores']} events"
            })

            highest_pct_sess = max(analyzed, key=lambda s: s['snoring_percentage'])
            records.append({
                'category': 'HIGHEST SNORING %',
                'session_id': highest_pct_sess['session_id'],
                'value': f"{highest_pct_sess['snoring_percentage']:.1f}%"
            })

            highest_rate_sess = max(analyzed, key=lambda s: s['events_per_minute'])
            records.append({
                'category': 'HIGHEST EVENTS/MIN',
                'session_id': highest_rate_sess['session_id'],
                'value': f"{highest_rate_sess['events_per_minute']:.1f} ev/min"
            })

            longest_sess = max(analyzed, key=lambda s: s['duration'])
            records.append({
                'category': 'LONGEST SESSION',
                'session_id': longest_sess['session_id'],
                'value': f"{longest_sess['duration']:.1f} sec"
            })

        return {
            'records_notice': "Records from this SNORESCAN installation only.",
            'records': records
        }
