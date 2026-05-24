/** Register service worker and optional Web Push for patients */
(function () {
  const API = window.location.origin;

  function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const raw = atob(base64);
    const out = new Uint8Array(raw.length);
    for (let i = 0; i < raw.length; ++i) out[i] = raw.charCodeAt(i);
    return out;
  }

  async function registerServiceWorker() {
    if (!('serviceWorker' in navigator)) return null;
    try {
      return await navigator.serviceWorker.register('/sw.js', { scope: '/' });
    } catch (e) {
      console.warn('SW registration failed', e);
      return null;
    }
  }

  async function subscribePatientPush(patientId) {
    if (!patientId || !('PushManager' in window)) return;
    try {
      const reg = await navigator.serviceWorker.ready;
      const perm = await Notification.requestPermission();
      if (perm !== 'granted') return;

      const res = await fetch(`${API}/push/vapid-public-key`);
      const { publicKey } = await res.json();
      if (!publicKey) return;

      let sub = await reg.pushManager.getSubscription();
      if (!sub) {
        sub = await reg.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: urlBase64ToUint8Array(publicKey),
        });
      }
      await fetch(`${API}/patient/push-subscribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patient_id: parseInt(patientId, 10), subscription: sub.toJSON() }),
      });
    } catch (e) {
      console.warn('Push subscribe skipped', e);
    }
  }

  window.SwasthPWA = { registerServiceWorker, subscribePatientPush };

  document.addEventListener('DOMContentLoaded', () => {
    registerServiceWorker();
    const pid = localStorage.getItem('patient_id');
    if (pid && document.body.classList.contains('patient-dashboard')) {
      subscribePatientPush(pid);
    }
  });
})();
