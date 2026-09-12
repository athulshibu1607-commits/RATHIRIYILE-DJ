import math
import logging

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')


class PatternAnalyzer:
    """
    Performs Phase 6 Snoring Pattern & Possible-Indicator Analysis.
    Analyzes stored SQLite snore events for frequency, duration, intensity,
    spectral variation, clustering, spacing gaps, non-medical acoustic observations,
    and fun hackathon snore personalities & roommate survival scores.
    """

    PERSONALITIES = [
        ("Gentle Kitten Purr", "Soft, low-frequency rhythmic breathing with minimal acoustic rumble."),
        ("Sleepy Panda", "Occasional gentle snore bursts with calm, quiet intermissions."),
        ("Motorcycle Mode", "Moderate event frequency with steady, low-pitched acoustic idling."),
        ("Tractor Mode", "Frequent low-frequency chugging with prominent acoustic rumble."),
        ("Heavy Machinery Mode", "Continuous, intense acoustic activity demanding heavy-duty soundproofing."),
        ("Darth Vader Mode", "Heavy, dramatic respiratory inhalation with deep harmonic reverberation."),
        ("Thunder Engine", "High-intensity acoustic blasts with large peak amplitude spikes."),
        ("Nuclear Alarm Clock", "Extremely frequent, loud, and continuous acoustic activity capable of waking entire households.")
    ]

    def analyze_session_events(self, events: list, session_duration_sec: float) -> dict:
        """
        Calculates complete Phase 6 pattern breakdown from real session snore events.
        Guaranteed zero-division and zero-event safety without crashes.
        """
        session_duration = max(1.0, float(session_duration_sec))
        total_events = len(events)

        if not events or total_events == 0:
            return self._empty_pattern_analysis(session_duration)

        # Auto-compute start_offset_sec if missing (e.g., when fetched directly from SQLite)
        for idx, e in enumerate(events):
            if 'start_offset_sec' not in e or e.get('start_offset_sec') is None:
                gap = float(e.get('time_since_prev_snore', 0.0))
                if idx == 0:
                    e['start_offset_sec'] = gap
                else:
                    prev_end = float(events[idx-1].get('start_offset_sec', 0.0)) + float(events[idx-1].get('duration_seconds', 0.0))
                    e['start_offset_sec'] = prev_end + gap

        # Extract event metric arrays
        durations = [float(e.get('duration_seconds', 0.0)) for e in events]
        intensities = [float(e.get('intensity_db', -80.0)) for e in events]
        rms_vals = [float(e.get('rms_energy', 0.0)) for e in events]
        peak_vals = [float(e.get('peak_amplitude', 0.0)) for e in events]
        freqs = [float(e.get('dominant_freq_hz', 0.0)) for e in events]
        confidences = [float(e.get('confidence', 0.0)) for e in events]

        centroids = [float(e.get('spectral_centroid', 0.0)) for e in events]
        bandwidths = [float(e.get('spectral_bandwidth', 0.0)) for e in events]
        rolloffs = [float(e.get('spectral_rolloff', 0.0)) for e in events]
        flatness_vals = [float(e.get('spectral_flatness', 0.0)) for e in events]

        low_energies = [float(e.get('low_frequency_energy', 0.0)) for e in events]
        mid_energies = [float(e.get('mid_frequency_energy', 0.0)) for e in events]
        high_energies = [float(e.get('high_frequency_energy', 0.0)) for e in events]

        def safe_mean(arr, default=0.0):
            return float(sum(arr) / len(arr)) if arr else float(default)

        # A. Snoring Frequency
        events_per_minute = float((total_events / session_duration) * 60.0)
        if events_per_minute < 2.0:
            frequency_classification = "Occasional"
        elif events_per_minute <= 5.0:
            frequency_classification = "Moderate"
        else:
            frequency_classification = "Frequent"

        # B. Snoring Duration
        total_snore_duration = float(sum(durations))
        avg_snore_duration = safe_mean(durations)
        shortest_snore = float(min(durations))
        longest_snore = float(max(durations))
        snoring_percentage = float((total_snore_duration / session_duration) * 100.0)

        # C. Event Spacing & Clustering (Within 10s gap threshold)
        event_spacings = []
        clusters = []
        current_cluster = [events[0]]

        for i in range(1, total_events):
            # Calculate gap between event[i-1] and event[i]
            prev_end = float(events[i-1].get('start_offset_sec', 0.0)) + float(events[i-1].get('duration_seconds', 0.0))
            curr_start = float(events[i].get('start_offset_sec', prev_end + 5.0))
            gap = max(0.0, curr_start - prev_end)
            event_spacings.append(gap)

            if gap <= 10.0:
                current_cluster.append(events[i])
            else:
                if len(current_cluster) >= 2:
                    clusters.append(current_cluster)
                current_cluster = [events[i]]

        if len(current_cluster) >= 2:
            clusters.append(current_cluster)

        avg_event_spacing = safe_mean(event_spacings, 0.0)
        cluster_count = len(clusters)
        largest_cluster = max([len(c) for c in clusters]) if clusters else (1 if total_events > 0 else 0)
        avg_events_per_cluster = safe_mean([len(c) for c in clusters], 0.0) if clusters else 0.0

        # D. Intensity Metrics & Classification
        avg_intensity_db = safe_mean(intensities, -80.0)
        max_intensity_db = float(max(intensities))
        min_intensity_db = float(min(intensities))
        avg_rms = safe_mean(rms_vals)
        max_peak = float(max(peak_vals))

        if avg_intensity_db < -45.0:
            intensity_pattern = "Low Intensity"
        elif avg_intensity_db <= -30.0:
            intensity_pattern = "Moderate Intensity"
        else:
            intensity_pattern = "High Intensity"

        # E. Frequency Features & Variation
        avg_dominant_freq_hz = safe_mean(freqs)
        min_dominant_freq_hz = float(min(freqs))
        max_dominant_freq_hz = float(max(freqs))

        if HAS_NUMPY and len(freqs) > 1:
            freq_std_dev = float(np.std(freqs))
        else:
            variance = sum((x - avg_dominant_freq_hz) ** 2 for x in freqs) / max(1, len(freqs))
            freq_std_dev = math.sqrt(variance)

        if freq_std_dev < 30.0:
            frequency_pattern = "Relatively Stable"
        elif freq_std_dev <= 80.0:
            frequency_pattern = "Moderately Varying"
        else:
            frequency_pattern = "Highly Varying"

        # F. Duration Pattern
        if avg_snore_duration < 0.5:
            duration_pattern = "Mostly Short Events"
        elif avg_snore_duration <= 1.5:
            duration_pattern = "Mixed Duration Events"
        else:
            duration_pattern = "Several Longer Events"

        # G. Possible Irregular Acoustic Pattern Detection
        spacing_std = float(np.std(event_spacings)) if (HAS_NUMPY and len(event_spacings) > 1) else 0.0
        irregular_pattern = bool(
            freq_std_dev > 60.0 or
            spacing_std > 15.0 or
            (cluster_count >= 2 and avg_event_spacing > 12.0)
        )

        irregular_explanation = ""
        if irregular_pattern:
            irregular_explanation = "Possible irregular acoustic pattern observed. Event spacing and spectral frequencies varied substantially, with several short clusters separated by longer quiet periods."

        # H. Acoustic Pattern Observations (Readable Non-Medical Sentences)
        observations = []

        if frequency_classification == "Frequent":
            observations.append(f"Frequent acoustic events were detected ({events_per_minute:.1f} events/min).")
        elif frequency_classification == "Moderate":
            observations.append(f"Moderate frequency of acoustic events observed ({events_per_minute:.1f} events/min).")
        else:
            observations.append(f"Occasional acoustic events detected across session ({events_per_minute:.1f} events/min).")

        if cluster_count > 0:
            observations.append(f"Several events occurred in closely spaced clusters ({cluster_count} clusters, largest: {largest_cluster} events).")

        if frequency_pattern == "Relatively Stable":
            observations.append(f"Detected events showed relatively consistent low-frequency characteristics (avg {avg_dominant_freq_hz:.0f} Hz).")
        else:
            observations.append(f"Acoustic frequencies showed {frequency_pattern.lower()} characteristics ({min_dominant_freq_hz:.0f} Hz to {max_dominant_freq_hz:.0f} Hz).")

        if duration_pattern == "Several Longer Events":
            observations.append(f"Several longer acoustic events were detected (longest: {longest_snore:.1f}s).")
        else:
            observations.append(f"Event durations averaged {avg_snore_duration:.1f}s ({duration_pattern.lower()}).")

        # I. Fun Hackathon Personality Classification
        if events_per_minute > 10.0 and max_intensity_db > -20.0:
            personality, desc = self.PERSONALITIES[7]  # Nuclear Alarm Clock
        elif max_intensity_db > -18.0 and avg_dominant_freq_hz < 220.0:
            personality, desc = self.PERSONALITIES[6]  # Thunder Engine
        elif total_events > 15 and avg_dominant_freq_hz < 180.0:
            personality, desc = self.PERSONALITIES[5]  # Darth Vader Mode
        elif events_per_minute > 6.0 and max_intensity_db > -25.0:
            personality, desc = self.PERSONALITIES[4]  # Heavy Machinery
        elif events_per_minute > 4.0 and max_intensity_db > -35.0:
            personality, desc = self.PERSONALITIES[3]  # Tractor Mode
        elif events_per_minute > 2.0:
            personality, desc = self.PERSONALITIES[2]  # Motorcycle Mode
        elif total_events > 2:
            personality, desc = self.PERSONALITIES[1]  # Sleepy Panda
        else:
            personality, desc = self.PERSONALITIES[0]  # Gentle Kitten Purr

        # J. Roommate Survival Score (100 - Snore Impact)
        snore_impact = (
            (snoring_percentage * 0.4) +
            (min(50.0, events_per_minute * 5.0) * 0.3) +
            (max(0.0, avg_intensity_db + 70.0) * 0.3)
        )
        survival_score = max(0.0, round(100.0 - snore_impact, 1))
        snore_score = round(min(100.0, snore_impact * 1.2), 1)

        funny_verdict = f"{personality}: {desc} Roommates recommend earplug protection level {int(max(1, 10 - survival_score / 10))}."

        avg_confidence = safe_mean(confidences)
        avg_spectral_centroid = safe_mean(centroids)
        avg_spectral_bandwidth = safe_mean(bandwidths)
        avg_spectral_rolloff = safe_mean(rolloffs)
        avg_spectral_flatness = safe_mean(flatness_vals)

        low_frequency_energy = safe_mean(low_energies)
        mid_frequency_energy = safe_mean(mid_energies)
        high_frequency_energy = safe_mean(high_energies)

        # K. Phase 9 Advanced Calculations
        # Strongest events (top 3)
        sorted_by_intensity = sorted(events, key=lambda x: float(x.get('intensity_db', -80.0)), reverse=True)
        strongest_events = []
        for e in sorted_by_intensity[:3]:
            strongest_events.append({
                'event_number': e.get('event_number', e.get('id', 1)),
                'intensity_db': round(float(e.get('intensity_db', -80.0)), 1),
                'duration_seconds': round(float(e.get('duration_seconds', 0.0)), 2),
                'dominant_freq_hz': round(float(e.get('dominant_freq_hz', 0.0)), 1),
                'start_time': e.get('start_time', ''),
                'confidence': round(float(e.get('confidence', 0.0)), 1)
            })

        # Longest events (top 3)
        sorted_by_duration = sorted(events, key=lambda x: float(x.get('duration_seconds', 0.0)), reverse=True)
        longest_events = []
        for e in sorted_by_duration[:3]:
            longest_events.append({
                'event_number': e.get('event_number', e.get('id', 1)),
                'duration_seconds': round(float(e.get('duration_seconds', 0.0)), 2),
                'intensity_db': round(float(e.get('intensity_db', -80.0)), 1),
                'dominant_freq_hz': round(float(e.get('dominant_freq_hz', 0.0)), 1),
                'start_time': e.get('start_time', ''),
                'confidence': round(float(e.get('confidence', 0.0)), 1)
            })

        # Quiet period analysis
        first_event_start = float(events[0].get('start_offset_sec', 0.0))
        last_event_end = float(events[-1].get('start_offset_sec', 0.0)) + float(events[-1].get('duration_seconds', 0.0))
        quiet_before_first = round(max(0.0, first_event_start), 1)
        quiet_after_last = round(max(0.0, session_duration - last_event_end), 1)
        longest_quiet_between = round(max(event_spacings), 1) if event_spacings else 0.0
        longest_quiet_period = round(max(quiet_before_first, quiet_after_last, longest_quiet_between), 1)
        total_quiet_duration = round(max(0.0, session_duration - total_snore_duration), 1)
        quiet_percentage = round(min(100.0, (total_quiet_duration / session_duration) * 100.0), 1)

        # Detailed event spacing list
        event_spacings_details = []
        for i in range(1, total_events):
            event_spacings_details.append({
                'from_event': events[i-1].get('event_number', i),
                'to_event': events[i].get('event_number', i+1),
                'spacing_sec': round(event_spacings[i-1], 1)
            })

        # Activity Heatmap (Divide session into up to 10 segments)
        num_segments = min(10, max(1, int(session_duration / 3.0)))
        seg_duration = max(1.0, session_duration / float(num_segments))
        activity_heatmap = []

        for s in range(num_segments):
            s_start = s * seg_duration
            s_end = (s + 1) * seg_duration
            s_events = [e for e in events if s_start <= float(e.get('start_offset_sec', 0.0)) < s_end]
            s_snore_dur = sum(float(e.get('duration_seconds', 0.0)) for e in s_events)

            if s_snore_dur >= (seg_duration * 0.25) or len(s_events) >= 2:
                act_level = "High"
            elif len(s_events) == 1 or s_snore_dur > 0:
                act_level = "Low"
            else:
                act_level = "Quiet"

            activity_heatmap.append({
                'segment': s + 1,
                'time_range': f"{int(s_start)}s–{int(s_end)}s",
                'activity_level': act_level,
                'event_count': len(s_events)
            })

        return {
            'total_events': total_events,
            'total_snores': total_events,
            'total_snore_duration': round(total_snore_duration, 2),
            'avg_snore_duration': round(avg_snore_duration, 2),
            'shortest_snore': round(shortest_snore, 2),
            'longest_snore': round(longest_snore, 2),
            'snoring_percentage': round(min(100.0, snoring_percentage), 1),
            'quiet_percentage': quiet_percentage,
            'total_quiet_duration': total_quiet_duration,
            'events_per_minute': round(events_per_minute, 1),
            'frequency_classification': frequency_classification,
            'avg_event_spacing': round(avg_event_spacing, 1),
            'event_spacings': [round(s, 1) for s in event_spacings],
            'cluster_count': cluster_count,
            'largest_cluster': largest_cluster,
            'avg_events_per_cluster': round(avg_events_per_cluster, 1),
            'avg_intensity_db': round(avg_intensity_db, 1),
            'max_intensity_db': round(max_intensity_db, 1),
            'min_intensity_db': round(min_intensity_db, 1),
            'avg_rms': round(avg_rms, 6),
            'max_peak': round(max_peak, 6),
            'dominant_freq_hz': round(avg_dominant_freq_hz, 1),
            'min_dominant_freq_hz': round(min_dominant_freq_hz, 1),
            'max_dominant_freq_hz': round(max_dominant_freq_hz, 1),
            'freq_std_dev': round(freq_std_dev, 1),
            'intensity_pattern': intensity_pattern,
            'frequency_pattern': frequency_pattern,
            'duration_pattern': duration_pattern,
            'irregular_pattern': irregular_pattern,
            'irregular_explanation': irregular_explanation,
            'observations': observations,
            'avg_spectral_centroid': round(avg_spectral_centroid, 1),
            'avg_spectral_bandwidth': round(avg_spectral_bandwidth, 1),
            'avg_spectral_rolloff': round(avg_spectral_rolloff, 1),
            'avg_spectral_flatness': round(avg_spectral_flatness, 4),
            'low_frequency_energy': round(low_frequency_energy, 4),
            'mid_frequency_energy': round(mid_frequency_energy, 4),
            'high_frequency_energy': round(high_frequency_energy, 4),
            'avg_confidence': round(avg_confidence, 1),
            'snore_score': snore_score,
            'snore_personality': personality,
            'survival_score': survival_score,
            'funny_verdict': funny_verdict,
            # Phase 9 additions
            'strongest_events': strongest_events,
            'longest_events': longest_events,
            'quiet_before_first': quiet_before_first,
            'quiet_after_last': quiet_after_last,
            'longest_quiet_between': longest_quiet_between,
            'longest_quiet_period': longest_quiet_period,
            'event_spacings_details': event_spacings_details,
            'activity_heatmap': activity_heatmap
        }

    def _empty_pattern_analysis(self, session_duration_sec: float) -> dict:
        sess_dur = round(max(0.0, float(session_duration_sec)), 1)
        return {
            'total_events': 0,
            'total_snores': 0,
            'total_snore_duration': 0.0,
            'avg_snore_duration': 0.0,
            'shortest_snore': 0.0,
            'longest_snore': 0.0,
            'snoring_percentage': 0.0,
            'quiet_percentage': 100.0,
            'total_quiet_duration': sess_dur,
            'events_per_minute': 0.0,
            'frequency_classification': "None",
            'avg_event_spacing': 0.0,
            'cluster_count': 0,
            'largest_cluster': 0,
            'avg_events_per_cluster': 0.0,
            'avg_intensity_db': -80.0,
            'max_intensity_db': -80.0,
            'min_intensity_db': -80.0,
            'avg_rms': 0.0,
            'max_peak': 0.0,
            'dominant_freq_hz': 0.0,
            'min_dominant_freq_hz': 0.0,
            'max_dominant_freq_hz': 0.0,
            'freq_std_dev': 0.0,
            'intensity_pattern': "Silent",
            'frequency_pattern': "N/A",
            'duration_pattern': "None",
            'irregular_pattern': False,
            'irregular_explanation': "",
            'observations': ["Not enough data for a meaningful pattern observation. Peaceful silence detected."],
            'avg_spectral_centroid': 0.0,
            'avg_spectral_bandwidth': 0.0,
            'avg_spectral_rolloff': 0.0,
            'avg_spectral_flatness': 0.0,
            'low_frequency_energy': 0.0,
            'mid_frequency_energy': 0.0,
            'high_frequency_energy': 0.0,
            'avg_confidence': 0.0,
            'snore_score': 0.0,
            'snore_personality': 'Gentle Kitten Purr',
            'survival_score': 100.0,
            'funny_verdict': 'Gentle Kitten Purr: Soft, rhythmic breathing with minimal acoustic rumble. Peaceful room.',
            # Phase 9 additions
            'strongest_events': [],
            'longest_events': [],
            'quiet_before_first': sess_dur,
            'quiet_after_last': 0.0,
            'longest_quiet_between': 0.0,
            'longest_quiet_period': sess_dur,
            'event_spacings': [],
            'event_spacings_details': [],
            'activity_heatmap': [{'segment': 1, 'time_range': f"0s–{int(sess_dur)}s", 'activity_level': 'Quiet', 'event_count': 0}]
        }

    def compare_sessions(self, session_ids: list) -> dict:
        """
        Calculates side-by-side Phase 10 comparisons for a list of session IDs.
        """
        from database.db import get_session, get_session_events

        if not session_ids or len(session_ids) < 2:
            return {
                'status': 'error',
                'message': 'Select at least 2 sessions to compare.',
                'sessions': [],
                'changes': [],
                'snore_battle': None,
                'roommate_survival_comparison': None
            }

        sessions_data = []
        for s_id in session_ids:
            sess = get_session(s_id)
            if not sess:
                continue
            events = get_session_events(s_id)
            stats = self.analyze_session_events(events, sess.get('duration_seconds', 0.0))
            
            sessions_data.append({
                'session_id': sess['id'],
                'date': str(sess.get('start_time', 'N/A'))[:10],
                'start_time': str(sess.get('start_time', 'N/A')),
                'duration': round(float(sess.get('duration_seconds', 0.0)), 1),
                'event_count': stats.get('total_snores', 0),
                'snoring_duration': stats.get('total_snore_duration', 0.0),
                'snoring_percentage': stats.get('snoring_percentage', 0.0),
                'avg_event_duration': stats.get('avg_snore_duration', 0.0),
                'longest_event': stats.get('longest_snore', 0.0),
                'avg_intensity': stats.get('avg_intensity_db', -80.0),
                'max_intensity': stats.get('max_intensity_db', -80.0),
                'avg_frequency': stats.get('dominant_freq_hz', 0.0),
                'events_per_minute': stats.get('events_per_minute', 0.0),
                'avg_spacing': stats.get('avg_event_spacing', 0.0),
                'cluster_count': stats.get('cluster_count', 0),
                'largest_cluster': stats.get('largest_cluster', 0),
                'survival_score': stats.get('survival_score', 100.0),
                'snore_score': stats.get('snore_score', 0.0),
                'snore_personality': stats.get('snore_personality', 'Gentle Kitten Purr')
            })

        if len(sessions_data) < 2:
            return {
                'status': 'error',
                'message': 'Select at least 2 valid sessions to compare.',
                'sessions': sessions_data,
                'changes': [],
                'snore_battle': None,
                'roommate_survival_comparison': None
            }

        # 1. Session Change Analysis
        changes = []
        for i in range(1, len(sessions_data)):
            prev_s = sessions_data[i-1]
            curr_s = sessions_data[i]
            
            pct_diff = round(curr_s['snoring_percentage'] - prev_s['snoring_percentage'], 1)
            evt_diff = curr_s['event_count'] - prev_s['event_count']
            rate_diff = round(curr_s['events_per_minute'] - prev_s['events_per_minute'], 1)
            int_diff = round(curr_s['avg_intensity'] - prev_s['avg_intensity'], 1)
            dur_diff = round(curr_s['avg_event_duration'] - prev_s['avg_event_duration'], 2)

            if pct_diff > 0:
                trend_direction = "increased"
                wording = f"Acoustic activity increased by {abs(pct_diff)}%."
            elif pct_diff < 0:
                trend_direction = "decreased"
                wording = f"Acoustic activity decreased by {abs(pct_diff)}%."
            else:
                trend_direction = "unchanged"
                wording = "Acoustic activity remained unchanged."

            changes.append({
                'from_session': prev_s['session_id'],
                'to_session': curr_s['session_id'],
                'snoring_percentage_change': pct_diff,
                'event_count_change': evt_diff,
                'events_per_minute_change': rate_diff,
                'avg_intensity_change': int_diff,
                'avg_duration_change': dur_diff,
                'trend_direction': trend_direction,
                'neutral_wording': wording
            })

        # 2. Fun Session Battle
        sorted_by_activity = sorted(sessions_data, key=lambda s: (s['snoring_percentage'], s['avg_intensity']), reverse=True)
        winner_s = sorted_by_activity[0]
        runner_s = sorted_by_activity[-1]

        if winner_s['snoring_percentage'] == runner_s['snoring_percentage'] and winner_s['avg_intensity'] == runner_s['avg_intensity']:
            battle_verdict = "Both sessions were equally quiet."
            battle_winner_id = "Tie"
        else:
            battle_verdict = f"SESSION #{winner_s['session_id']} wins the SNORE BATTLE!"
            battle_winner_id = winner_s['session_id']

        snore_battle = {
            'session_a': sessions_data[0]['session_id'],
            'session_b': sessions_data[-1]['session_id'],
            'winner_session_id': battle_winner_id,
            'verdict': battle_verdict,
            'entertainment_notice': "Entertainment feature based on acoustic amplitude and event density."
        }

        # 3. Roommate Survival Comparison
        sorted_by_survival = sorted(sessions_data, key=lambda s: s['survival_score'], reverse=True)
        best_survival = sorted_by_survival[0]

        roommate_survival = {
            'scores': [{'session_id': s['session_id'], 'survival_score': s['survival_score']} for s in sessions_data],
            'best_session_id': best_survival['session_id'],
            'best_score': best_survival['survival_score'],
            'verdict': f"Better roommate survival: Session #{best_survival['session_id']}"
        }

        return {
            'status': 'success',
            'sessions': sessions_data,
            'changes': changes,
            'snore_battle': snore_battle,
            'roommate_survival_comparison': roommate_survival
        }

    def calculate_trends(self) -> dict:
        """
        Calculates chronological trend data across all stored SQLite sessions.
        """
        from database.db import get_all_sessions, get_session_events

        sessions = get_all_sessions()
        if not sessions:
            return {
                'status': 'success',
                'has_trends': False,
                'total_sessions': 0,
                'message': 'No sessions recorded yet.',
                'sessions': []
            }

        chrono_sessions = sorted(sessions, key=lambda s: str(s.get('start_time', '')))

        trend_series = []
        for s in chrono_sessions:
            events = get_session_events(s['id'])
            stats = self.analyze_session_events(events, s.get('duration_seconds', 0.0))
            trend_series.append({
                'session_id': s['id'],
                'date': str(s.get('start_time', 'N/A'))[:10],
                'start_time': str(s.get('start_time', 'N/A')),
                'duration': round(float(s.get('duration_seconds', 0.0)), 1),
                'total_snores': stats['total_snores'],
                'snoring_percentage': stats['snoring_percentage'],
                'events_per_minute': stats['events_per_minute'],
                'avg_intensity_db': stats['avg_intensity_db'],
                'avg_snore_duration': stats['avg_snore_duration'],
                'snore_personality': stats['snore_personality'],
                'survival_score': stats['survival_score']
            })

        has_trends = len(trend_series) >= 2
        message = "" if has_trends else "More sessions are needed to identify a trend."

        return {
            'status': 'success',
            'has_trends': has_trends,
            'total_sessions': len(trend_series),
            'message': message,
            'sessions': trend_series
        }

    def calculate_overall_statistics(self) -> dict:
        """
        Calculates all-time aggregate statistics across all sessions in SQLite.
        """
        from database.db import get_all_sessions, get_session_events

        sessions = get_all_sessions()
        if not sessions:
            return {
                'total_sessions': 0,
                'total_monitoring_time': 0.0,
                'total_events': 0,
                'total_snoring_time': 0.0,
                'overall_avg_snoring_percentage': 0.0,
                'overall_avg_events_per_minute': 0.0,
                'overall_avg_intensity': -80.0,
                'overall_avg_event_duration': 0.0,
                'longest_event_ever': 0.0,
                'highest_intensity_ever': -80.0,
                'highest_frequency_ever': 0.0,
                'most_active_session': None,
                'quietest_session': None,
                'most_intense_session': None
            }

        analyzed_sessions = []
        all_events = []

        total_dur = 0.0
        total_snore_dur = 0.0
        total_evts = 0

        for s in sessions:
            events = get_session_events(s['id'])
            stats = self.analyze_session_events(events, s.get('duration_seconds', 0.0))
            
            s_dur = float(s.get('duration_seconds', 0.0))
            total_dur += s_dur
            total_snore_dur += stats['total_snore_duration']
            total_evts += stats['total_snores']
            all_events.extend(events)

            analyzed_sessions.append({
                'session_id': s['id'],
                'date': str(s.get('start_time', 'N/A'))[:10],
                'start_time': str(s.get('start_time', 'N/A')),
                'duration': round(s_dur, 1),
                'event_count': stats['total_snores'],
                'snoring_percentage': stats['snoring_percentage'],
                'events_per_minute': stats['events_per_minute'],
                'avg_intensity': stats['avg_intensity_db'],
                'max_intensity': stats['max_intensity_db'],
                'avg_event_duration': stats['avg_snore_duration'],
                'longest_event': stats['longest_snore'],
                'snore_personality': stats['snore_personality'],
                'survival_score': stats['survival_score']
            })

        overall_avg_snoring_percentage = round((total_snore_dur / total_dur * 100.0), 1) if total_dur > 0 else 0.0
        overall_avg_events_per_minute = round((total_evts / total_dur * 60.0), 1) if total_dur > 0 else 0.0
        
        valid_intensities = [s['avg_intensity'] for s in analyzed_sessions if s['event_count'] > 0]
        overall_avg_intensity = round(sum(valid_intensities) / len(valid_intensities), 1) if valid_intensities else -80.0
        
        valid_durations = [s['avg_event_duration'] for s in analyzed_sessions if s['event_count'] > 0]
        overall_avg_event_duration = round(sum(valid_durations) / len(valid_durations), 2) if valid_durations else 0.0

        longest_event_ever = round(max([s['longest_event'] for s in analyzed_sessions]), 2) if analyzed_sessions else 0.0
        highest_intensity_ever = round(max([s['max_intensity'] for s in analyzed_sessions]), 1) if analyzed_sessions else -80.0
        
        all_freqs = [float(e.get('dominant_freq_hz', 0.0)) for e in all_events]
        highest_frequency_ever = round(max(all_freqs), 1) if all_freqs else 0.0

        most_active_session = max(analyzed_sessions, key=lambda x: x['snoring_percentage']) if analyzed_sessions else None
        quietest_session = min(analyzed_sessions, key=lambda x: x['snoring_percentage']) if analyzed_sessions else None
        most_intense_session = max(analyzed_sessions, key=lambda x: x['avg_intensity']) if analyzed_sessions else None

        return {
            'total_sessions': len(sessions),
            'total_monitoring_time': round(total_dur, 1),
            'total_events': total_evts,
            'total_snoring_time': round(total_snore_dur, 1),
            'overall_avg_snoring_percentage': overall_avg_snoring_percentage,
            'overall_avg_events_per_minute': overall_avg_events_per_minute,
            'overall_avg_intensity': overall_avg_intensity,
            'overall_avg_event_duration': overall_avg_event_duration,
            'longest_event_ever': longest_event_ever,
            'highest_intensity_ever': highest_intensity_ever,
            'highest_frequency_ever': highest_frequency_ever,
            'most_active_session': most_active_session,
            'quietest_session': quietest_session,
            'most_intense_session': most_intense_session
        }
