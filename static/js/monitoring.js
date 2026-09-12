/**
 * SNORESCAN Phase 7 & Phase 12 - Live Monitoring Dashboard Manager
 * Supports hardware PCM mic capture & isolated Demo Mode.
 */

let activeSessionId = null;
let statusPollInterval = null;
let isMonitoringActive = false;
let animationFrameId = null;
let latestIntensityHistory = [];
let detectedEventsList = [];
let demoTimerSec = 0;
let demoInterval = null;

function formatTimer(sec) {
    if (!sec || isNaN(sec)) return "00:00:00";
    const hrs = Math.floor(sec / 3600).toString().padStart(2, '0');
    const mins = Math.floor((sec % 3600) / 60).toString().padStart(2, '0');
    const secs = Math.floor(sec % 60).toString().padStart(2, '0');
    return `${hrs}:${mins}:${secs}`;
}

async function startMonitoringSession() {
    const startBtn = document.getElementById('monStartBtn');
    const stopBtn = document.getElementById('monStopBtn');

    // Double-click protection & loading state
    if (startBtn) startBtn.disabled = true;
    if (stopBtn) stopBtn.disabled = true;

    hideMicError();

    // Check if running in Demo Mode
    if (window.IS_DEMO_MODE) {
        startDemoMonitoring();
        return;
    }

    try {
        const permissionGranted = await window.snoreRecorder.requestMicPermission();
        if (!permissionGranted) {
            throw new Error('Microphone permission was denied or is unavailable. Allow microphone access and try again.');
        }

        updateDashboardStatus('STARTING...', false);
        const response = await fetch('/api/monitoring/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ capture_mode: 'browser' })
        });
        const data = await response.json();

        if (data.status === 'success') {
            activeSessionId = data.session_id;
            isMonitoringActive = true;
            window.snoreRecorder.startCapture(activeSessionId);

            const grid = document.getElementById('liveDetectionsGrid');
            if (grid) {
                grid.innerHTML = `
                    <div style="grid-column: 1 / -1; text-align: center; padding: 30px; color: var(--text-muted); font-size: 14px;">
                        <i class="fa-solid fa-microphone-lines" style="font-size: 24px; margin-bottom: 8px; display: block;"></i>
                        Continuous microphone capture active. Waiting for acoustic events...
                    </div>`;
            }

            updateDashboardStatus('MONITORING', true, data.session_id, data.start_time_str);
            if (window.DayNightWorld) window.DayNightWorld.transitionToNight();
            startStatusPolling();
            startCanvasAnimations();
            console.log(`Monitoring Session #${activeSessionId} started.`);
        } else {
            showMicError(`🎙️ SNORESCAN couldn't access your microphone. ${data.message || 'Please check your microphone permissions and try again.'}`);
            updateDashboardStatus('READY', false);
        }

    } catch (err) {
        console.error("Failed to start session:", err);
        if (window.snoreRecorder) await window.snoreRecorder.stopMicStream();
        showMicError(`🎙️ SNORESCAN couldn't access your microphone. ${err.message || 'Please check your microphone permissions and try again.'}`);
        updateDashboardStatus('READY', false);
    }
}

async function stopMonitoringSession() {
    const startBtn = document.getElementById('monStartBtn');
    const stopBtn = document.getElementById('monStopBtn');

    // Double-click protection
    if (startBtn) startBtn.disabled = true;
    if (stopBtn) stopBtn.disabled = true;

    if (window.IS_DEMO_MODE) {
        stopDemoMonitoring();
        return;
    }

    if (!activeSessionId && !isMonitoringActive) {
        updateDashboardStatus('READY', false);
        return;
    }

    updateDashboardStatus('STOPPING...', false);

    try {
        if (window.snoreRecorder) await window.snoreRecorder.stopMicStream();
        const response = await fetch('/api/monitoring/stop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: activeSessionId })
        });
        const data = await response.json();

        if (data.status === 'success') {
            const finishedSessionId = data.session_id || activeSessionId;
            activeSessionId = null;
            isMonitoringActive = false;

            stopStatusPolling();
            stopCanvasAnimations();
            updateDashboardStatus('COMPLETED', false, finishedSessionId);

            if (window.DayNightWorld) window.DayNightWorld.transitionToDay();

            // Redirect to final report
            setTimeout(() => {
                window.location.href = `/report/${finishedSessionId}`;
            }, 600);
        } else {

            console.error("Error stopping session:", data.message);
            updateDashboardStatus('READY', false);
        }
    } catch (err) {
        console.error("Failed to stop session:", err);
        updateDashboardStatus('READY', false);
    }
}

function startDemoMonitoring() {
    isMonitoringActive = true;
    activeSessionId = 'DEMO-999';
    demoTimerSec = 0;
    detectedEventsList = [];

    updateDashboardStatus('MONITORING', true, 'DEMO-999', '23:00:00');
    startCanvasAnimations();

    if (demoInterval) clearInterval(demoInterval);
    demoInterval = setInterval(() => {
        demoTimerSec += 1;
        const timerElem = document.getElementById('dashTimer');
        if (timerElem) timerElem.innerText = formatTimer(demoTimerSec);

        // Simulate periodic demo events
        if (demoTimerSec === 5 || demoTimerSec === 18 || demoTimerSec === 32) {
            const evtNum = detectedEventsList.length + 1;
            const newEvt = {
                event_number: evtNum,
                time_str: new Date().toLocaleTimeString(),
                duration: 2.5 + evtNum,
                intensity_dbfs: -18.0 - (evtNum * 3),
                dominant_frequency: 140 + (evtNum * 20),
                confidence: 94
            };
            detectedEventsList.push(newEvt);
            renderLiveEventCards(detectedEventsList);

            const eventCountElem = document.getElementById('dashEventCount');
            if (eventCountElem) eventCountElem.innerText = detectedEventsList.length;

            const snorePctElem = document.getElementById('dashSnorePct');
            if (snorePctElem) snorePctElem.innerText = `${((detectedEventsList.length * 3.5 / demoTimerSec) * 100).toFixed(1)}%`;
        }
    }, 1000);
}

function stopDemoMonitoring() {
    isMonitoringActive = false;
    if (demoInterval) clearInterval(demoInterval);
    stopCanvasAnimations();
    updateDashboardStatus('COMPLETED', false, 'DEMO-999');
    window.location.href = '/demo/report';
}

function startStatusPolling() {
    stopStatusPolling();
    fetchLiveStatus();
    statusPollInterval = setInterval(fetchLiveStatus, 400);
}

function stopStatusPolling() {
    if (statusPollInterval) {
        clearInterval(statusPollInterval);
        statusPollInterval = null;
    }
}

async function fetchLiveStatus() {
    if (window.IS_DEMO_MODE) return;
    try {
        const response = await fetch('/api/monitoring/status');
        const data = await response.json();

        if (data.monitoring) {
            isMonitoringActive = true;
            activeSessionId = data.session_id;
            updateDashboardStatus('MONITORING', true, data.session_id, data.start_time_str);
        } else if (isMonitoringActive && !data.monitoring) {
            isMonitoringActive = false;
            stopStatusPolling();
            updateDashboardStatus('COMPLETED', false, activeSessionId);
        }

        const micBadge = document.getElementById('micBadge');
        if (micBadge) {
            if (data.mic_connected && !data.stream_error) {
                micBadge.className = 'status-badge badge-live';
                micBadge.innerHTML = `<i class="fa-solid fa-microphone"></i> Hardware Mic Active: ${data.device_name || 'System Microphone'}`;
                hideMicError();
            } else if (data.stream_error) {
                showMicError(`🎙️ SNORESCAN couldn't access your microphone: ${data.stream_error}`);
            }
        }

        const timerElem = document.getElementById('dashTimer');
        if (timerElem) timerElem.innerText = formatTimer(data.duration || 0);

        const eventCountElem = document.getElementById('dashEventCount');
        const durationElem = document.getElementById('dashDuration');
        const snoreDurationElem = document.getElementById('dashSnoreDuration');
        const snorePctElem = document.getElementById('dashSnorePct');
        const avgIntensityElem = document.getElementById('dashAvgIntensity');
        const latestFreqElem = document.getElementById('dashLatestFreq');
        const minMaxFreqElem = document.getElementById('dashMinMaxFreq');
        const currentDbElem = document.getElementById('dashCurrentDb');

        if (eventCountElem) eventCountElem.innerText = data.event_count || 0;
        if (durationElem) durationElem.innerText = `${(data.duration || 0).toFixed(1)} s`;
        if (snoreDurationElem) snoreDurationElem.innerText = `${(data.snoring_duration || 0).toFixed(1)} s`;
        if (snorePctElem) snorePctElem.innerText = `${(data.snoring_percentage || 0).toFixed(1)}%`;
        if (avgIntensityElem) avgIntensityElem.innerText = `${(data.average_intensity || -80).toFixed(1)} dBFS`;
        if (latestFreqElem) latestFreqElem.innerText = data.latest_frequency ? `${Math.round(data.latest_frequency)} Hz` : '0 Hz';
        if (minMaxFreqElem) minMaxFreqElem.innerText = `${Math.round(data.min_frequency || 0)} / ${Math.round(data.max_frequency || 0)} Hz`;
        if (currentDbElem) currentDbElem.innerText = `${(data.current_db || -80).toFixed(1)} dBFS`;

        if (Array.isArray(data.intensity_history)) {
            latestIntensityHistory = data.intensity_history;
        }

        if (Array.isArray(data.events)) {
            renderLiveEventCards(data.events);
        }

    } catch (err) {
        console.warn("Error polling monitoring status:", err);
    }
}

function renderLiveEventCards(events) {
    const grid = document.getElementById('liveDetectionsGrid');
    if (!grid) return;

    if (!events || events.length === 0) {
        grid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 30px; color: var(--text-muted); font-size: 14px;">
                <i class="fa-solid fa-microphone-lines" style="font-size: 24px; margin-bottom: 8px; display: block;"></i>
                No snore events detected yet. Continuous microphone monitoring active.
            </div>`;
        return;
    }

    const sortedEvents = [...events].reverse();

    grid.innerHTML = sortedEvents.map((evt, idx) => {
        const evtNumStr = evt.event_number ? evt.event_number.toString().padStart(2, '0') : (events.length - idx).toString().padStart(2, '0');
        return `
            <div class="event-detection-card">
                <div class="event-card-header">
                    <span class="event-card-title"><i class="fa-solid fa-bell text-amber"></i> EVENT #${evtNumStr}</span>
                    <span class="event-card-time">${evt.time_str || '--:--:--'}</span>
                </div>
                <div class="event-card-metrics">
                    <div class="event-metric-item">
                        <span class="event-metric-label">Duration</span>
                        <span class="event-metric-val text-violet">${(evt.duration || 0).toFixed(2)} s</span>
                    </div>
                    <div class="event-metric-item">
                        <span class="event-metric-label">Intensity</span>
                        <span class="event-metric-val text-cyan">${(evt.intensity_dbfs || -80).toFixed(1)} dBFS</span>
                    </div>
                    <div class="event-metric-item">
                        <span class="event-metric-label">Frequency</span>
                        <span class="event-metric-val text-emerald">${evt.dominant_frequency ? Math.round(evt.dominant_frequency) : 0} Hz</span>
                    </div>
                    <div class="event-metric-item">
                        <span class="event-metric-label">Confidence</span>
                        <span class="event-metric-val text-amber">${evt.confidence || 90}%</span>
                    </div>
                </div>
            </div>`;
    }).join('');
}

function updateDashboardStatus(statusState, isMonitoring, sessionId = null, startTimeStr = null) {
    const badge = document.getElementById('dashStatusBadge');
    const dot = document.getElementById('dashStatusDot');
    const text = document.getElementById('dashStatusText');
    const startBtn = document.getElementById('monStartBtn');
    const stopBtn = document.getElementById('monStopBtn');
    const infoSessionId = document.getElementById('infoSessionId');
    const infoStartTime = document.getElementById('infoStartTime');

    if (badge && dot && text) {
        badge.className = `live-status-badge live-status-${statusState.toLowerCase().replace(/[^a-z]/g, '')}`;
        text.innerText = statusState;

        if (statusState === 'MONITORING') {
            dot.className = 'pulse-dot anim-pulse';
        } else {
            dot.className = 'pulse-dot';
        }
    }

    if (startBtn) startBtn.disabled = isMonitoring;
    if (stopBtn) stopBtn.disabled = !isMonitoring;

    if (infoSessionId && sessionId) infoSessionId.innerText = `#${sessionId}`;
    if (infoStartTime && startTimeStr) infoStartTime.innerText = startTimeStr;
}

function showMicError(msg) {
    const errorCard = document.getElementById('micErrorCard');
    const errorMsg = document.getElementById('micErrorMessage');
    if (errorCard && errorMsg) {
        errorMsg.innerText = msg;
        errorCard.classList.remove('hidden');
    }
}

function hideMicError() {
    const errorCard = document.getElementById('micErrorCard');
    if (errorCard) errorCard.classList.add('hidden');
}

function startCanvasAnimations() {
    stopCanvasAnimations();

    const waveCanvas = document.getElementById('liveWaveformCanvas');
    const graphCanvas = document.getElementById('liveIntensityCanvas');

    function renderLoop() {
        if (waveCanvas) renderWaveform(waveCanvas);
        if (graphCanvas) renderIntensityGraph(graphCanvas);
        animationFrameId = requestAnimationFrame(renderLoop);
    }
    renderLoop();
}

function stopCanvasAnimations() {
    if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
        animationFrameId = null;
    }
}

function renderWaveform(canvas) {
    const ctx = canvas.getContext('2d');
    const width = canvas.width = canvas.parentElement.clientWidth || 400;
    const height = canvas.height = 140;

    ctx.fillStyle = '#0b0f19';
    ctx.fillRect(0, 0, width, height);

    ctx.strokeStyle = 'rgba(255,255,255,0.05)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, height / 2);
    ctx.lineTo(width, height / 2);
    ctx.stroke();

    ctx.strokeStyle = isMonitoringActive ? '#06b6d4' : '#64748b';
    ctx.lineWidth = 2;
    ctx.beginPath();

    const points = 50;
    const sliceWidth = width / points;
    let x = 0;

    for (let i = 0; i < points; i++) {
        let y = height / 2;
        if (isMonitoringActive) {
            const amplitude = Math.sin(i * 0.3 + Date.now() * 0.005) * 20;
            y += amplitude;
        }
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
        x += sliceWidth;
    }
    ctx.stroke();
}

function renderIntensityGraph(canvas) {
    const ctx = canvas.getContext('2d');
    const width = canvas.width = canvas.parentElement.clientWidth || 400;
    const height = canvas.height = 140;

    ctx.fillStyle = '#0b0f19';
    ctx.fillRect(0, 0, width, height);

    // Threshold line -35 dBFS
    const threshY = height - (((-35 + 80) / 80) * height);
    ctx.strokeStyle = 'rgba(244,63,94,0.4)';
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(0, threshY);
    ctx.lineTo(width, threshY);
    ctx.stroke();
    ctx.setLineDash([]);

    if (latestIntensityHistory.length === 0) return;

    ctx.strokeStyle = '#a855f7';
    ctx.lineWidth = 2;
    ctx.beginPath();

    const step = width / (latestIntensityHistory.length - 1 || 1);
    latestIntensityHistory.forEach((db, i) => {
        const x = i * step;
        const normDb = Math.max(-80, Math.min(0, db));
        const y = height - (((normDb + 80) / 80) * height);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.stroke();
}
