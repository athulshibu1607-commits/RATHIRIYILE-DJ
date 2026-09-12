/**
 * SNORESCAN Phase 13 — True Background Day/Night Orbital Engine
 * 100% Background Orbit Animation (Zero Overlays, Zero Modals, Zero Transition UI)
 */

class DayNightWorldManager {
  constructor() {
    this.mode = 'DAY'; // 'DAY' | 'NIGHT' | 'TRANSITIONING'
    this.isReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    this.animFrameId = null;
    this.initBackgroundEnvironment();
  }

  initBackgroundEnvironment() {
    if (!document.getElementById('day-night-background')) {
      const bg = document.createElement('div');
      bg.id = 'day-night-background';
      bg.innerHTML = `
        <div class="stars-layer" id="stars-container"></div>
        <div class="clouds-layer">
          <div class="cloud" style="top: 15%; left: -10%; width: 140px; height: 40px; animation-duration: 50s;"></div>
          <div class="cloud" style="top: 45%; left: -20%; width: 200px; height: 60px; animation-duration: 65s; animation-delay: 5s;"></div>
          <div class="cloud" style="top: 75%; left: -15%; width: 160px; height: 50px; animation-duration: 55s; animation-delay: 12s;"></div>
        </div>
        <div class="celestial-sun" id="celestial-sun">
          <div class="sun-rays"></div>
        </div>
        <div class="celestial-moon" id="celestial-moon"></div>
      `;
      document.body.prepend(bg);
      this.generateStars();
      this.setPositionImmediate('DAY');
    }
  }

  generateStars() {
    const container = document.getElementById('stars-container');
    if (!container) return;
    container.innerHTML = '';
    for (let i = 0; i < 45; i++) {
      const star = document.createElement('div');
      star.className = 'star';
      const size = Math.random() * 3 + 1;
      star.style.width = `${size}px`;
      star.style.height = `${size}px`;
      star.style.top = `${Math.random() * 100}%`;
      star.style.left = `${Math.random() * 100}%`;
      star.style.animationDelay = `${Math.random() * 3}s`;
      star.style.animationDuration = `${Math.random() * 2 + 2}s`;
      container.appendChild(star);
    }
  }

  /**
   * Quadratic Bezier Curve Calculation: B(t) = (1-t)^2 * P0 + 2(1-t)t * P1 + t^2 * P2
   */
  getQuadraticPoint(p0, p1, p2, t) {
    const oneMinusT = 1 - t;
    return (
      oneMinusT * oneMinusT * p0 +
      2 * oneMinusT * t * p1 +
      t * t * p2
    );
  }

  /**
   * Immediately sets Sun and Moon coordinates based on static mode state
   */
  setPositionImmediate(targetMode) {
    const sun = document.getElementById('celestial-sun');
    const moon = document.getElementById('celestial-moon');
    if (!sun || !moon) return;

    if (targetMode === 'NIGHT') {
      document.body.classList.remove('day-mode');
      document.body.classList.add('night-mode');
      // Sun below horizon
      sun.style.left = '5vw';
      sun.style.top = '115vh';
      sun.style.opacity = '0';
      sun.style.transform = 'translate(-50%, -50%) scale(0.5)';
      // Moon in upper night sky
      moon.style.left = '50vw';
      moon.style.top = '18vh';
      moon.style.opacity = '1';
      moon.style.transform = 'translate(-50%, -50%) scale(1)';
      this.mode = 'NIGHT';
    } else {
      document.body.classList.remove('night-mode');
      document.body.classList.add('day-mode');
      // Sun in upper-right day position
      sun.style.left = '75vw';
      sun.style.top = '15vh';
      sun.style.opacity = '1';
      sun.style.transform = 'translate(-50%, -50%) scale(1)';
      // Moon below horizon
      moon.style.left = '-10vw';
      moon.style.top = '115vh';
      moon.style.opacity = '0';
      moon.style.transform = 'translate(-50%, -50%) scale(0.5)';
      this.mode = 'DAY';
    }
  }

  /**
   * Triggers continuous 60fps parametric orbital transition DAY -> NIGHT (Sunset & Moonrise)
   */
  transitionToNight(onComplete) {
    if (this.isReducedMotion) {
      this.setPositionImmediate('NIGHT');
      if (onComplete) onComplete();
      return;
    }

    if (this.animFrameId) cancelAnimationFrame(this.animFrameId);
    this.mode = 'TRANSITIONING';
    document.body.classList.remove('day-mode');
    document.body.classList.add('night-mode');

    const sun = document.getElementById('celestial-sun');
    const moon = document.getElementById('celestial-moon');
    const startTime = performance.now();
    const duration = 2200; // ms

    // SUNSET Bezier Control Points (Upper-right -> Middle -> Below lower-left horizon)
    const sunP0 = { x: 75, y: 15 };
    const sunP1 = { x: 40, y: 45 };
    const sunP2 = { x: 5, y: 115 };

    // MOONRISE Bezier Control Points (Lower-right horizon -> Right sky arc -> Upper-middle night sky)
    const moonP0 = { x: 95, y: 115 };
    const moonP1 = { x: 75, y: 50 };
    const moonP2 = { x: 50, y: 18 };

    const animateFrame = (currentTime) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(1, elapsed / duration);
      // Easing cubic ease-in-out
      const easeT = progress < 0.5
        ? 4 * progress * progress * progress
        : 1 - Math.pow(-2 * progress + 2, 3) / 2;

      if (sun) {
        const sx = this.getQuadraticPoint(sunP0.x, sunP1.x, sunP2.x, easeT);
        const sy = this.getQuadraticPoint(sunP0.y, sunP1.y, sunP2.y, easeT);
        const sScale = 1 - easeT * 0.5;
        const sOpacity = 1 - easeT;
        sun.style.left = `${sx}vw`;
        sun.style.top = `${sy}vh`;
        sun.style.opacity = `${sOpacity}`;
        sun.style.transform = `translate(-50%, -50%) scale(${sScale})`;
      }

      if (moon) {
        const mx = this.getQuadraticPoint(moonP0.x, moonP1.x, moonP2.x, easeT);
        const my = this.getQuadraticPoint(moonP0.y, moonP1.y, moonP2.y, easeT);
        const mScale = 0.5 + easeT * 0.5;
        const mOpacity = easeT;
        moon.style.left = `${mx}vw`;
        moon.style.top = `${my}vh`;
        moon.style.opacity = `${mOpacity}`;
        moon.style.transform = `translate(-50%, -50%) scale(${mScale})`;
      }

      if (progress < 1) {
        this.animFrameId = requestAnimationFrame(animateFrame);
      } else {
        this.mode = 'NIGHT';
        this.setPositionImmediate('NIGHT');
        if (onComplete) onComplete();
      }
    };

    this.animFrameId = requestAnimationFrame(animateFrame);
  }

  /**
   * Triggers continuous 60fps parametric orbital transition NIGHT -> DAY (Moonset & Sunrise)
   */
  transitionToDay(onComplete) {
    if (this.isReducedMotion) {
      this.setPositionImmediate('DAY');
      if (onComplete) onComplete();
      return;
    }

    if (this.animFrameId) cancelAnimationFrame(this.animFrameId);
    this.mode = 'TRANSITIONING';
    document.body.classList.remove('night-mode');
    document.body.classList.add('day-mode');

    const sun = document.getElementById('celestial-sun');
    const moon = document.getElementById('celestial-moon');
    const startTime = performance.now();
    const duration = 2200; // ms

    // MOONSET Bezier Control Points (Upper-middle night sky -> Left curve -> Below lower-left horizon)
    const moonP0 = { x: 50, y: 18 };
    const moonP1 = { x: 25, y: 45 };
    const moonP2 = { x: -10, y: 115 };

    // SUNRISE Bezier Control Points (Lower-right horizon -> Right sky arc -> Upper-right day sky)
    const sunP0 = { x: 95, y: 115 };
    const sunP1 = { x: 85, y: 50 };
    const sunP2 = { x: 75, y: 15 };

    const animateFrame = (currentTime) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(1, elapsed / duration);
      const easeT = progress < 0.5
        ? 4 * progress * progress * progress
        : 1 - Math.pow(-2 * progress + 2, 3) / 2;

      if (moon) {
        const mx = this.getQuadraticPoint(moonP0.x, moonP1.x, moonP2.x, easeT);
        const my = this.getQuadraticPoint(moonP0.y, moonP1.y, moonP2.y, easeT);
        const mScale = 1 - easeT * 0.5;
        const mOpacity = 1 - easeT;
        moon.style.left = `${mx}vw`;
        moon.style.top = `${my}vh`;
        moon.style.opacity = `${mOpacity}`;
        moon.style.transform = `translate(-50%, -50%) scale(${mScale})`;
      }

      if (sun) {
        const sx = this.getQuadraticPoint(sunP0.x, sunP1.x, sunP2.x, easeT);
        const sy = this.getQuadraticPoint(sunP0.y, sunP1.y, sunP2.y, easeT);
        const sScale = 0.5 + easeT * 0.5;
        const sOpacity = easeT;
        sun.style.left = `${sx}vw`;
        sun.style.top = `${sy}vh`;
        sun.style.opacity = `${sOpacity}`;
        sun.style.transform = `translate(-50%, -50%) scale(${sScale})`;
      }

      if (progress < 1) {
        this.animFrameId = requestAnimationFrame(animateFrame);
      } else {
        this.mode = 'DAY';
        this.setPositionImmediate('DAY');
        if (onComplete) onComplete();
      }
    };

    this.animFrameId = requestAnimationFrame(animateFrame);
  }

  pulseAudioEvent() {
    const moon = document.getElementById('celestial-moon');
    if (moon && this.mode === 'NIGHT') {
      moon.style.boxShadow = '0 0 60px rgba(56, 189, 248, 1)';
      setTimeout(() => {
        moon.style.boxShadow = '';
      }, 400);
    }
  }
}

// Global Singleton Instance
window.DayNightWorld = new DayNightWorldManager();

/* ==========================================================================
   Snore Boss Battle Frontend Engine
   ========================================================================== */

function initBossBattle(bossData) {
  if (!bossData) return;

  let currentHP = bossData.hp;
  const maxHP = bossData.max_hp;

  const hpBar = document.getElementById('boss-hp-bar');
  const hpText = document.getElementById('boss-hp-text');
  const log = document.getElementById('boss-battle-log');
  const bossIcon = document.getElementById('boss-icon');

  const updateHPUI = () => {
    const pct = Math.max(0, Math.min(100, (currentHP / maxHP) * 100));
    if (hpBar) hpBar.style.width = `${pct}%`;
    if (hpText) hpText.textContent = `${currentHP} / ${maxHP} HP`;
  };

  const triggerHitAnimation = () => {
    if (bossIcon) {
      bossIcon.classList.add('hit');
      setTimeout(() => bossIcon.classList.remove('hit'), 400);
    }
  };

  window.handleBossAction = function (action) {
    if (currentHP <= 0) {
      if (log) log.textContent = '🏆 THE SNORE BOSS HAS ALREADY BEEN DEFEATED!';
      return;
    }

    if (action === 'attack') {
      const dmg = Math.floor(Math.random() * 25) + 15;
      currentHP = Math.max(0, currentHP - dmg);
      updateHPUI();
      triggerHitAnimation();

      if (currentHP <= 0) {
        if (log) log.textContent = '💥 CRITICAL HIT! YOU DEFEATED THE SNORE BOSS! 🏆';
        if (bossIcon) bossIcon.style.opacity = '0.3';
      } else {
        if (log) log.textContent = `⚔️ CRITICAL HIT! Dealt ${dmg} damage to ${bossData.name}!`;
      }
    } else if (action === 'defend') {
      if (log) log.textContent = `🛡️ BLOCKED! You blocked ${bossData.special_move}!`;
    } else if (action === 'run') {
      if (log) log.textContent = '🏃 YOU ESCAPED! (The Snore Boss is still sleeping...)';
    } else if (action === 'surrender') {
      if (log) log.textContent = '💀 HONEST SURRENDER. You accepted your snoring fate.';
    }
  };

  updateHPUI();
}

/* ==========================================================================
   Snore Court Frontend Handler
   ========================================================================== */

function initSnoreCourt() {
  window.selectCulprit = function (culprit) {
    fetch(`/api/boss/court?culprit=${encodeURIComponent(culprit)}`)
      .then(res => res.json())
      .then(data => {
        const box = document.getElementById('court-verdict-box');
        if (box && data.status === 'success') {
          box.innerHTML = `
            <strong>⚖️ VERDICT FOR ${data.culprit.toUpperCase()}:</strong><br/>
            ${data.verdict}<br/>
            <em>${data.sentence}</em>
          `;
          box.style.display = 'block';
        }
      })
      .catch(() => {
        const box = document.getElementById('court-verdict-box');
        if (box) {
          box.innerHTML = `<strong>⚖️ VERDICT:</strong> GUILTY AS CHARGED! The evidence against ${culprit} is overwhelming!`;
          box.style.display = 'block';
        }
      });
  };
}

/* ==========================================================================
   Guess The Snore Trivia Handler
   ========================================================================== */

function initGuessTheSnore() {
  window.answerTrivia = function (isCorrect, btn) {
    const feedback = document.getElementById('trivia-feedback');
    const buttons = document.querySelectorAll('.trivia-opt-btn');
    buttons.forEach(b => b.disabled = true);

    if (isCorrect) {
      if (btn) btn.style.background = '#22c55e';
      if (feedback) {
        feedback.innerHTML = '✅ <strong>CORRECT!</strong> You recognized the authentic snoring spectrum pattern!';
        feedback.style.color = '#22c55e';
      }
    } else {
      if (btn) btn.style.background = '#ef4444';
      if (feedback) {
        feedback.innerHTML = '❌ <strong>INCORRECT!</strong> That acoustic signature was actually a real detected snore event!';
        feedback.style.color = '#ef4444';
      }
    }
  };
}

document.addEventListener('DOMContentLoaded', () => {
  initSnoreCourt();
  initGuessTheSnore();
});
