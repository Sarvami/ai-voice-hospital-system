/* ── dark-toggle.js — include on every page ── */

(function () {

  const saved = localStorage.getItem('theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);

  document.addEventListener('DOMContentLoaded', () => {

    /* ── Inject styles ── */
    const style = document.createElement('style');
    style.textContent = `
      #themeToggleWrap {
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 9999;
        display: flex;
        align-items: center;
        gap: 8px;
        background: rgba(13, 27, 46, 0.85);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 999px;
        padding: 6px 14px 6px 10px;
        backdrop-filter: blur(12px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.35);
        cursor: pointer;
        transition: box-shadow 0.2s, transform 0.2s;
        user-select: none;
      }
      [data-theme="light"] #themeToggleWrap {
        background: rgba(255,255,255,0.85);
        border-color: rgba(0,0,0,0.1);
        box-shadow: 0 4px 16px rgba(0,0,0,0.12);
      }
      #themeToggleWrap:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 28px rgba(0,0,0,0.4);
      }
      #themeToggleTrack {
        width: 36px;
        height: 20px;
        border-radius: 999px;
        background: #1a3a5c;
        position: relative;
        transition: background 0.3s;
        flex-shrink: 0;
      }
      [data-theme="light"] #themeToggleTrack {
        background: #f0a500;
      }
      #themeToggleKnob {
        position: absolute;
        top: 3px;
        left: 3px;
        width: 14px;
        height: 14px;
        border-radius: 50%;
        background: #4fc3f7;
        transition: transform 0.3s, background 0.3s;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 9px;
      }
      [data-theme="light"] #themeToggleKnob {
        transform: translateX(16px);
        background: #fff;
      }
      #themeToggleLabel {
        font-family: 'Sora', 'Inter', sans-serif;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.5px;
        color: #a0aec0;
        transition: color 0.3s;
      }
      [data-theme="light"] #themeToggleLabel {
        color: #4a5568;
      }
    `;
    document.head.appendChild(style);

    /* ── Build toggle ── */
    const wrap  = document.createElement('div');
    wrap.id = 'themeToggleWrap';

    const track = document.createElement('div');
    track.id = 'themeToggleTrack';

    const knob  = document.createElement('div');
    knob.id = 'themeToggleKnob';

    const label = document.createElement('span');
    label.id = 'themeToggleLabel';

    const current = localStorage.getItem('theme') || 'dark';
    label.textContent = current === 'dark' ? '☀️ Light' : '🌙 Dark';

    track.appendChild(knob);
    wrap.appendChild(track);
    wrap.appendChild(label);
    document.body.appendChild(wrap);

    /* ── Toggle handler ── */
    wrap.addEventListener('click', () => {
      const now  = document.documentElement.getAttribute('data-theme');
      const next = now === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('theme', next);
      label.textContent = next === 'dark' ? '☀️ Light' : '🌙 Dark';
    });

  });

})();