/** Patient first-time guided walkthrough */
(function () {
  const STORAGE_KEY = 'swasthseva_onboarding_done';

  const STEPS = [
    {
      title: 'Welcome to SwasthSeva',
      text: 'Book doctor appointments using your voice in English, Hindi, or Marathi — right from the home page.',
    },
    {
      title: 'Your dashboard',
      text: 'See upcoming visits, medical records, and messages from your care team in one place.',
    },
    {
      title: 'Stay notified',
      text: 'Allow notifications when prompted so you never miss appointment updates or hospital announcements.',
    },
  ];

  function shouldShow() {
    return !localStorage.getItem(STORAGE_KEY) && localStorage.getItem('patient_id');
  }

  function buildOverlay() {
    let step = 0;
    const overlay = document.createElement('div');
    overlay.className = 'onboarding-overlay';
    overlay.id = 'onboardingOverlay';

    function render() {
      const s = STEPS[step];
      overlay.innerHTML = `
        <div class="onboarding-card">
          <div class="onboarding-steps">
            ${STEPS.map((_, i) => `<span class="${i === step ? 'active' : ''}"></span>`).join('')}
          </div>
          <h2>${s.title}</h2>
          <p>${s.text}</p>
          <div class="onboarding-actions">
            <button type="button" class="btn-skip">Skip</button>
            <button type="button" class="btn-next">${step < STEPS.length - 1 ? 'Next' : 'Get started'}</button>
          </div>
        </div>`;
      overlay.querySelector('.btn-skip').onclick = finish;
      overlay.querySelector('.btn-next').onclick = () => {
        if (step < STEPS.length - 1) {
          step += 1;
          render();
        } else {
          finish();
        }
      };
    }

    function finish() {
      localStorage.setItem(STORAGE_KEY, '1');
      overlay.classList.add('hidden');
      overlay.remove();
      if (window.SwasthPWA && localStorage.getItem('patient_id')) {
        window.SwasthPWA.subscribePatientPush(localStorage.getItem('patient_id'));
      }
    }

    render();
    return overlay;
  }

  window.initPatientOnboarding = function () {
    if (!shouldShow()) return;
    document.body.appendChild(buildOverlay());
  };
})();
