import os
from flask import Flask, render_template, jsonify, request, redirect, url_for
from database import (
    init_db,
    create_session,
    end_session,
    get_session,
    get_all_sessions,
    get_session_events,
    record_snore_event
)
from analysis import (
    AudioProcessor,
    recorder_manager,
    SnoreDetector,
    FrequencyAnalyzer,
    FeatureExtractor,
    PatternAnalyzer,
    FunAnalyzer,
    BossAnalyzer
)
from ml import SnoreClassifier

app = Flask(__name__)

# Initialize database schema on startup
with app.app_context():
    init_db()

# Initialize analysis engines
audio_processor = AudioProcessor()
snore_detector = SnoreDetector()
frequency_analyzer = FrequencyAnalyzer()
feature_extractor = FeatureExtractor()
pattern_analyzer = PatternAnalyzer()
fun_analyzer = FunAnalyzer()
boss_analyzer = BossAnalyzer()
snore_classifier = SnoreClassifier()



@app.route('/')
def index():
    """Renders SNORESCAN main home dashboard."""
    return render_template('index.html')


@app.route('/monitoring')
def monitoring():
    """Renders real-time audio monitoring page."""
    return render_template('monitoring.html')


@app.route('/analysis')
def analysis():
    """Renders spectral & acoustic feature analysis view."""
    return render_template('analysis.html')


@app.route('/useless')
def useless_hub():
    """Renders standalone SNORESCAN Useless Intelligence™ Hub."""
    streak = fun_analyzer.get_snore_streak()
    world_records = fun_analyzer.get_world_records()
    hall_of_fame = fun_analyzer.get_hall_of_fame()
    hall_of_shame = boss_analyzer.get_hall_of_shame()
    return render_template(
        'useless.html',
        streak=streak,
        world_records=world_records,
        hall_of_fame=hall_of_fame,
        hall_of_shame=hall_of_shame
    )


@app.route('/history')
def history():
    """Renders historical monitoring sessions with Phase 10 multi-session metrics."""
    raw_sessions = get_all_sessions()
    sessions = []
    for s in raw_sessions:
        events = get_session_events(s['id'])
        stats = pattern_analyzer.analyze_session_events(events, s.get('duration_seconds', 0.0))
        s_dict = dict(s)
        s_dict['total_snore_duration'] = stats['total_snore_duration']
        s_dict['avg_dominant_freq_hz'] = stats['dominant_freq_hz']
        s_dict['avg_snore_duration'] = stats['avg_snore_duration']
        s_dict['longest_snore'] = stats['longest_snore']
        s_dict['snore_personality'] = stats['snore_personality']
        s_dict['survival_score'] = stats['survival_score']
        sessions.append(s_dict)
    return render_template('history.html', sessions=sessions)


@app.route('/compare')
def compare():
    """Renders multi-session comparison dashboard."""
    ids_str = request.args.get('ids', '')
    session_ids = []
    if ids_str:
        try:
            session_ids = [int(i.strip()) for i in ids_str.split(',') if i.strip().isdigit()]
        except Exception:
            session_ids = []

    comparison = pattern_analyzer.compare_sessions(session_ids)
    trends = pattern_analyzer.calculate_trends()
    stats = pattern_analyzer.calculate_overall_statistics()
    raw_sessions = get_all_sessions()

    return render_template(
        'compare.html',
        comparison=comparison,
        trends=trends,
        stats=stats,
        all_sessions=raw_sessions,
        selected_ids=session_ids
    )


@app.route('/report/<int:session_id>')
def report(session_id):
    """Renders comprehensive session analysis report with Phase 4 spectral & Phase 11 fun metrics."""
    session = get_session(session_id)
    if not session:
        return redirect(url_for('history'))
    events = get_session_events(session_id)
    
    # Calculate Phase 4 session aggregate statistics
    session_duration = session.get('duration_seconds', 0.0)
    stats = pattern_analyzer.analyze_session_events(events, session_duration)

    # Compute Phase 11 fun features
    fun_data = fun_analyzer.analyze_fun_features(session_id, session, events, stats)

    # Compute Phase 13 Boss & Trivia data
    boss_data = boss_analyzer.generate_boss(session_id, session, stats, events)
    trivia_data = boss_analyzer.get_guess_the_snore_trivia(session_id, events)

    # Compute Real FFT spectrum from WAV audio file for detected events (Option C: Average FFT Spectrum)
    spectrum_chart = frequency_analyzer.compute_session_fft_spectrum(session_id)

    return render_template(
        'report.html',
        session=session,
        events=events,
        stats=stats,
        fun_data=fun_data,
        boss_data=boss_data,
        trivia_data=trivia_data,
        spectrum_chart=spectrum_chart
    )


@app.route('/status')
def status():
    """Renders system status & component health check page."""
    return render_template('status.html')


@app.route('/api/status')
def api_status():
    """API endpoint returning live component health check status."""
    mic_status = "🟢 Microphone System (Ready)"
    if recorder_manager.stream_error:
        mic_status = f"🔴 Microphone Error ({recorder_manager.stream_error})"
    elif recorder_manager.is_recording:
        mic_status = "🟢 Microphone System (Active Capture)"

    return jsonify({
        'status': 'success',
        'components': {
            'microphone_system': mic_status,
            'audio_analyzer': "🟢 Audio Analyzer (Operational)",
            'snore_detector': "🟢 Snore Detector (Operational)",
            'sqlite_database': "🟢 SQLite Database (Connected)",
            'pattern_analyzer': "🟢 Pattern Analyzer (Operational)",
            'fun_analyzer': "🟢 Fun Analyzer (Operational)",
            'boss_analyzer': "🟢 Boss Analyzer (Operational)"
        }
    })


@app.route('/demo')
@app.route('/demo/monitoring')
def demo_monitoring():
    """Renders live monitoring dashboard in Demo Mode (Isolated from SQLite)."""
    return render_template('monitoring.html', is_demo=True)


@app.route('/demo/report')
def demo_report():
    """Renders interactive session report in Demo Mode with reproducible fictional data."""
    demo_session = {
        'id': 'DEMO-999',
        'start_time': '2026-09-11 23:00:00',
        'end_time': '2026-09-11 23:30:00',
        'duration_seconds': 1800.0,
        'total_chunks': 900,
        'total_snores': 18,
        'total_snore_duration': 210.0,
        'avg_snore_duration': 11.6,
        'longest_snore': 14.5,
        'avg_intensity_db': -22.4,
        'max_intensity_db': -12.1,
        'avg_rms': 0.045,
        'max_peak': 0.18,
        'dominant_freq_hz': 145.2,
        'snoring_percentage': 11.6,
        'avg_confidence': 0.92,
        'snore_score': 68.5,
        'snore_personality': '🚜 TRACTOR MODE',
        'survival_score': 54.2,
        'funny_verdict': 'Your bedroom sounds like a tractor farm.',
        'audio_file_path': '',
        'status': 'completed'
    }
    demo_events = [
        {'id': 1, 'session_id': 'DEMO-999', 'event_number': 1, 'start_time': '23:02:10', 'end_time': '23:02:18', 'duration_seconds': 8.0, 'intensity_db': -24.1, 'peak_amplitude': 0.12, 'rms_energy': 0.035, 'dominant_freq_hz': 135.0, 'confidence': 91.0, 'start_offset_sec': 130.0},
        {'id': 2, 'session_id': 'DEMO-999', 'event_number': 2, 'start_time': '23:08:45', 'end_time': '23:08:59', 'duration_seconds': 14.5, 'intensity_db': -12.1, 'peak_amplitude': 0.18, 'rms_energy': 0.055, 'dominant_freq_hz': 110.0, 'confidence': 96.0, 'start_offset_sec': 525.0},
        {'id': 3, 'session_id': 'DEMO-999', 'event_number': 3, 'start_time': '23:15:20', 'end_time': '23:15:26', 'duration_seconds': 6.0, 'intensity_db': -28.0, 'peak_amplitude': 0.09, 'rms_energy': 0.025, 'dominant_freq_hz': 160.0, 'confidence': 88.0, 'start_offset_sec': 920.0}
    ]
    stats = pattern_analyzer.analyze_session_events(demo_events, 1800.0)
    fun_data = fun_analyzer.analyze_fun_features('DEMO-999', demo_session, demo_events, stats)
    boss_data = boss_analyzer.generate_boss(999, demo_session, stats, demo_events)
    trivia_data = boss_analyzer.get_guess_the_snore_trivia(999, demo_events)
    spectrum_chart = {'labels': [100, 200, 300, 400, 500], 'magnitudes': [0.5, 0.9, 0.4, 0.2, 0.1], 'has_data': True}

    return render_template(
        'report.html',
        session=demo_session,
        events=demo_events,
        stats=stats,
        fun_data=fun_data,
        boss_data=boss_data,
        trivia_data=trivia_data,
        spectrum_chart=spectrum_chart,
        is_demo=True
    )


@app.route('/api/boss/<int:session_id>')
def api_get_boss(session_id):
    """API endpoint returning deterministic Snore Boss data for a session."""
    session = get_session(session_id)
    if not session:
        return jsonify({'status': 'error', 'message': 'Session not found'}), 404
    events = get_session_events(session_id)
    stats = pattern_analyzer.analyze_session_events(events, session.get('duration_seconds', 0.0))
    boss_data = boss_analyzer.generate_boss(session_id, session, stats, events)
    trivia_data = boss_analyzer.get_guess_the_snore_trivia(session_id, events)
    return jsonify({
        'status': 'success',
        'boss': boss_data,
        'trivia': trivia_data
    })


@app.route('/api/boss/court')
def api_boss_court():
    """API endpoint returning deterministic Snore Court verdicts."""
    culprit = request.args.get('culprit', 'UNKNOWN ENTITY')
    verdict_data = boss_analyzer.get_snore_court_verdict(culprit)
    return jsonify({
        'status': 'success',
        'culprit': verdict_data['culprit'],
        'verdict': verdict_data['verdict'],
        'sentence': verdict_data['sentence']
    })



@app.errorhandler(404)
def not_found_error(error):
    if request.path.startswith('/api/'):
        return jsonify({'status': 'error', 'message': 'Resource not found'}), 404
    return redirect(url_for('index'))


@app.errorhandler(500)
def internal_error(error):
    if request.path.startswith('/api/'):
        return jsonify({'status': 'error', 'message': 'An internal server error occurred'}), 500
    return redirect(url_for('index'))


# --- API ENDPOINTS ---

@app.route('/api/monitoring/start', methods=['POST'])
def api_start_monitoring():
    """API endpoint to initiate continuous microphone capture for a new session."""
    session_id = create_session()
    started = recorder_manager.start_recording(session_id)
    
    if not started:
        return jsonify({
            'status': 'error',
            'session_id': session_id,
            'message': recorder_manager.stream_error or 'Failed to start microphone stream.'
        }), 500

    return jsonify({
        'status': 'success',
        'session_id': session_id,
        'device_name': recorder_manager.selected_device_name,
        'message': f'Microphone capture started for Session #{session_id}.'
    })


@app.route('/api/monitoring/status', methods=['GET'])
def api_monitoring_status():
    """API endpoint returning live real-time audio status and diagnostic metrics."""
    return jsonify(recorder_manager.get_live_status())


@app.route('/api/monitoring/stop', methods=['POST'])
def api_stop_monitoring():
    """API endpoint to conclude monitoring, flush audio to WAV, and store report stats."""
    data = request.get_json() or {}
    session_id = data.get('session_id')

    if not session_id:
        return jsonify({'status': 'error', 'message': 'Missing session_id'}), 400

    # Stop audio recording, flush pending snore events, and save WAV file
    rec_metrics = recorder_manager.stop_recording(session_id)

    # Fetch all detected events directly from SQLite for session_id (Single Source of Truth)
    events = get_session_events(session_id)
    actual_duration = rec_metrics.get('duration_seconds', 0.0)

    # Calculate Phase 4 aggregate statistics
    pattern_stats = pattern_analyzer.analyze_session_events(events, actual_duration)

    rec_metrics.update(pattern_stats)

    # Update SQLite database session record with complete metrics
    end_session(session_id, rec_metrics)

    return jsonify({
        'status': 'success',
        'session_id': session_id,
        'metrics': rec_metrics
    })


@app.route('/api/sessions', methods=['GET'])
@app.route('/api/sessions/all', methods=['GET'])
def api_get_sessions():
    """API endpoint returning JSON list of all sessions from SQLite."""
    sessions = get_all_sessions()
    return jsonify({'status': 'success', 'sessions': sessions})


@app.route('/api/sessions/compare', methods=['GET'])
def api_compare_sessions_route():
    """API endpoint returning JSON comparison breakdown for requested session IDs."""
    ids_str = request.args.get('ids', '')
    session_ids = []
    if ids_str:
        try:
            session_ids = [int(i.strip()) for i in ids_str.split(',') if i.strip().isdigit()]
        except Exception:
            session_ids = []

    res = pattern_analyzer.compare_sessions(session_ids)
    if res.get('status') == 'error':
        return jsonify(res), 400
    return jsonify(res)


@app.route('/api/sessions/trends', methods=['GET'])
def api_get_trends_route():
    """API endpoint returning chronological trend data across all stored sessions."""
    res = pattern_analyzer.calculate_trends()
    return jsonify(res)


@app.route('/api/sessions/statistics', methods=['GET'])
def api_get_statistics_route():
    """API endpoint returning all-time aggregate statistics across SQLite database."""
    res = pattern_analyzer.calculate_overall_statistics()
    return jsonify({'status': 'success', 'statistics': res})


@app.route('/api/sessions/<int:session_id>', methods=['GET'])
def api_get_session(session_id):
    """API endpoint returning JSON record for a single session."""
    session = get_session(session_id)
    if not session:
        return jsonify({'status': 'error', 'message': 'Session not found'}), 404
    events = get_session_events(session_id)
    return jsonify({
        'status': 'success',
        'session': session,
        'event_count': len(events)
    })


@app.route('/api/sessions/<int:session_id>/events', methods=['GET'])
def api_get_session_events_route(session_id):
    """API endpoint returning JSON list of all snore events recorded for a session."""
    session = get_session(session_id)
    if not session:
        return jsonify({'status': 'error', 'message': 'Session not found'}), 404
    events = get_session_events(session_id)
    return jsonify({
        'status': 'success',
        'session_id': session_id,
        'events': events,
        'total_events': len(events)
    })


@app.route('/api/sessions/<int:session_id>/patterns', methods=['GET'])
def api_get_session_patterns(session_id):
    """API endpoint returning Phase 6 JSON pattern analysis object for session_id."""
    session = get_session(session_id)
    if not session:
        return jsonify({'status': 'error', 'message': 'Session not found'}), 404
    events = get_session_events(session_id)
    patterns = pattern_analyzer.analyze_session_events(events, session.get('duration_seconds', 0.0))
    return jsonify({
        'status': 'success',
        'session_id': session_id,
        'patterns': patterns
    })


@app.route('/api/sessions/<int:session_id>/advanced-analysis', methods=['GET'])
def api_get_session_advanced_analysis(session_id):
    """API endpoint returning Phase 9 advanced analysis breakdown for session_id."""
    session = get_session(session_id)
    if not session:
        return jsonify({'status': 'error', 'message': 'Session not found'}), 404
    events = get_session_events(session_id)
    analysis_data = pattern_analyzer.analyze_session_events(events, session.get('duration_seconds', 0.0))
    return jsonify({
        'status': 'success',
        'session_id': session_id,
        'analysis': analysis_data
    })


@app.route('/api/sessions/<int:session_id>/fun-analysis', methods=['GET'])
def api_get_session_fun_analysis(session_id):
    """API endpoint returning Phase 11 fun & hackathon analysis breakdown for session_id."""
    session = get_session(session_id)
    if not session:
        return jsonify({'status': 'error', 'message': 'Session not found'}), 404
    events = get_session_events(session_id)
    stats = pattern_analyzer.analyze_session_events(events, session.get('duration_seconds', 0.0))
    fun_analysis = fun_analyzer.analyze_fun_features(session_id, session, events, stats)
    return jsonify({
        'status': 'success',
        'session_id': session_id,
        'fun_analysis': fun_analysis
    })


@app.route('/api/fun/hall-of-fame', methods=['GET'])
@app.route('/api/fun/world-records', methods=['GET'])
def api_get_fun_hall_of_fame():
    """API endpoint returning installation Hall of Fame and World Records."""
    res = fun_analyzer.get_hall_of_fame_and_world_records()
    return jsonify({'status': 'success', **res})


@app.route('/api/fun/streak', methods=['GET'])
def api_get_fun_streak():
    """API endpoint returning active snore streak statistics."""
    res = fun_analyzer.get_snore_streak()
    return jsonify({'status': 'success', **res})


@app.route('/api/fun/achievements', methods=['GET'])
def api_get_fun_achievements_all():
    """API endpoint returning overview of available achievement badges."""
    return jsonify({
        'status': 'success',
        'available_achievements': [
            '🏆 FIRST SNORE', '🔥 HOT ENGINE', '🚜 TRACTOR STARTED', '⚡ RAPID FIRE',
            '🌋 VOLCANIC', '🕰️ MARATHON SNORE', '🌌 DEEP SPACE', '💀 ROOMMATE DESTROYER',
            '👑 SNORE KING', '🏅 10 EVENTS', '🏅 50 EVENTS'
        ]
    })


@app.route('/api/sessions/<int:session_id>/export/csv', methods=['GET'])
@app.route('/report/<int:session_id>/csv', methods=['GET'])
def api_export_session_csv(session_id):
    """API endpoint to export session event data as downloadable CSV."""
    import csv
    import io
    from flask import Response

    session = get_session(session_id)
    if not session:
        return jsonify({'status': 'error', 'message': 'Session not found'}), 404

    events = get_session_events(session_id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Session ID', 'Event #', 'Start time', 'End time', 'Duration', 'RMS', 'Peak amplitude', 'dBFS', 'Dominant frequency', 'Confidence'])

    for idx, ev in enumerate(events, 1):
        writer.writerow([
            session_id,
            ev.get('event_number', idx),
            ev.get('start_time', ''),
            ev.get('end_time', ''),
            round(float(ev.get('duration_seconds', 0.0)), 2),
            round(float(ev.get('rms_energy', 0.0)), 6),
            round(float(ev.get('peak_amplitude', 0.0)), 4),
            round(float(ev.get('intensity_db', -80.0)), 1),
            round(float(ev.get('dominant_freq_hz', 0.0)), 1),
            round(float(ev.get('confidence', 0.0)), 1)
        ])

    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename=snorescan_session_{session_id}_events.csv'
    return response


@app.route('/api/sessions/compare/csv', methods=['GET'])
@app.route('/compare/csv', methods=['GET'])
def api_export_comparison_csv():
    """API endpoint to export multi-session comparison summary data as downloadable CSV."""
    import csv
    import io
    from flask import Response

    ids_str = request.args.get('ids', '')
    session_ids = []
    if ids_str:
        try:
            session_ids = [int(i.strip()) for i in ids_str.split(',') if i.strip().isdigit()]
        except Exception:
            session_ids = []

    res = pattern_analyzer.compare_sessions(session_ids)
    sessions = res.get('sessions', [])

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Session ID', 'Date', 'Duration', 'Event Count', 'Snoring Duration',
        'Snoring Percentage', 'Average Event Duration', 'Longest Event',
        'Average Intensity', 'Maximum Intensity', 'Average Frequency',
        'Events Per Minute', 'Average Spacing', 'Clusters', 'Largest Cluster',
        'Snore Score', 'Roommate Survival Score', 'Snore Personality'
    ])

    for s in sessions:
        writer.writerow([
            s.get('session_id', ''),
            s.get('date', ''),
            s.get('duration', 0.0),
            s.get('event_count', 0),
            s.get('snoring_duration', 0.0),
            s.get('snoring_percentage', 0.0),
            s.get('avg_event_duration', 0.0),
            s.get('longest_event', 0.0),
            s.get('avg_intensity', -80.0),
            s.get('max_intensity', -80.0),
            s.get('avg_frequency', 0.0),
            s.get('events_per_minute', 0.0),
            s.get('avg_spacing', 0.0),
            s.get('cluster_count', 0),
            s.get('largest_cluster', 0),
            s.get('snore_score', 0.0),
            s.get('survival_score', 100.0),
            s.get('snore_personality', '')
        ])

    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=snorescan_multi_session_comparison.csv'
    return response


if __name__ == '__main__':
    print("Starting SNORESCAN Web Server...")
    app.run(host='127.0.0.1', port=5000, debug=True)

