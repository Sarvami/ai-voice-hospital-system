/* ── theme.js — include on every page ── */

(function () {

  /* Apply saved theme immediately to avoid flash */
  const saved = localStorage.getItem('theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);

  /* Inject the toggle button once DOM is ready */
  document.addEventListener('DOMContentLoaded', () => {
    const btn = document.createElement('button');
    btn.id = 'themeToggle';
    btn.title = 'Toggle light/dark mode';
    btn.innerHTML = saved === 'dark' ? '☀️' : '🌙';
    btn.setAttribute('aria-label', 'Toggle theme');
    document.body.appendChild(btn);

    btn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme');
      const next    = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('theme', next);
      btn.innerHTML = next === 'dark' ? '☀️' : '🌙';
    });
  });

})();