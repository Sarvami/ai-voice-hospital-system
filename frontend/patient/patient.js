const BACKEND = window.location.origin;

/* ── XSS helper ── */
function esc(str) {
  if (str === null || str === undefined) return '—';
  return String(str).replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
}

/* ── Section navigation ── */
function showSection(section, liEl) {
  document.querySelectorAll(".section").forEach(sec => sec.classList.add("hidden"));
  document.getElementById(section).classList.remove("hidden");

  document.querySelectorAll(".sidebar li").forEach(l => l.classList.remove("active"));
  if (liEl) liEl.classList.add("active");
}

/* ── Load appointments ── */
async function loadAppointments() {
  const patientId = localStorage.getItem("patient_id");
  const table     = document.getElementById("appointmentsTable");
  const notifications = document.getElementById("appointmentNotifications");

  if (!patientId) {
    table.innerHTML = `<tr><td colspan="11" class="empty-row">Not logged in.</td></tr>`;
    if (notifications) notifications.innerHTML = "";
    return;
  }

  table.innerHTML = skeletonTableRows(11, 5);

  try {
    const res  = await fetch(`${BACKEND}/patient/appointments?patient_id=${patientId}`);
    const data = await res.json();
    const list = data.appointments || data;

    // Fetch meet links to map appointment_id → link
    let meetMap = {};
    try {
      const mRes = await fetch(`${BACKEND}/patient/meet-links?patient_id=${patientId}`);
      const mData = await mRes.json();
      (mData.meet_links || []).forEach(m => {
        if (m.appointment_id) meetMap[m.appointment_id] = m.meet_link;
      });
    } catch (_) {}

    table.innerHTML = "";

    if (!list || !list.length) {
      table.innerHTML = `<tr><td colspan="11" class="empty-row">No appointments found.</td></tr>`;
      if (notifications) notifications.innerHTML = "";
      return;
    }

    const cancelledByDoctor = list.filter(
      a => (a.status || "").toLowerCase() === "cancelled" && (a.cancelled_by || "").toLowerCase() === "doctor"
    );
    if (notifications) {
      notifications.innerHTML = cancelledByDoctor.map(a => `
        <div class="appointment-alert">
          <div class="alert-title">Appointment #${a.appointment_id || a.id} was cancelled by the doctor</div>
          <div class="alert-reason">${esc(a.cancellation_reason || "Doctor had an emergency.")}</div>
          <div class="alert-actions">
            <button class="alert-btn primary" onclick="rescheduleAppointment(${a.doctor_id || 0})">Reschedule</button>
            <button class="alert-btn secondary" onclick="bookAnotherDoctor()">Book Another Doctor</button>
          </div>
        </div>
      `).join("");
    }

    list.forEach(a => {
      const status = a.status || "Pending";
      let statusClass = "status-pending";
      if (status.toLowerCase() === "confirmed" || status.toLowerCase() === "scheduled") statusClass = "status-confirmed";
      else if (status.toLowerCase() === "cancelled") statusClass = "status-cancelled";
      else if (status.toLowerCase() === "completed") statusClass = "status-completed";

      const apptId = a.appointment_id || a.id;
      let actionHtml = "-";
      if (status.toLowerCase() === "completed") {
        if (a.rating) {
          actionHtml = `<span style="color:#f5a623">★ ${a.rating}/5</span>`;
        } else {
          actionHtml = `<button class="btn-rate" onclick="openRating(${apptId}, '${a.doctor || a.doctor_name}')">Rate Doctor</button>`;
        }
      }

      const meetLink = meetMap[apptId];
      const meetHtml = meetLink
        ? `<a href="${meetLink}" target="_blank" class="btn-meet"><i class="fa fa-video"></i> Join</a>`
        : '—';

      table.innerHTML += `
        <tr>
          <td>${apptId || "-"}</td>
          <td>${a.doctor || a.doctor_name || "-"}</td>
          <td>${a.doctor_phone || a.contact_phone || "-"}</td>
          <td>${a.doctor_email || a.email || "-"}</td>
          <td>${a.region || "-"}</td>
          <td>${a.date || "-"}</td>
          <td>${a.time || "-"}</td>
          <td><span class="status-badge ${statusClass}">${status}</span></td>
          <td>${esc(a.cancellation_reason || "-")}</td>
          <td>${meetHtml}</td>
          <td>
            <div class="action-cell">
              <button class="btn-chat-mini" title="Message Doctor" onclick="jumpToDoctorChat(${a.doctor_id}, '${esc(a.doctor || a.doctor_name)}')">
                <i class="fa fa-comments"></i>
              </button>
              <button class="btn-sos-mini" title="EMERGENCY" onclick="triggerSOS(${a.doctor_id}, '${esc(a.doctor || a.doctor_name)}')">
                <i class="fa fa-bell"></i> SOS
              </button>
              ${actionHtml !== '-' ? actionHtml : ''}
            </div>
          </td>
        </tr>
      `;
    });

    document.getElementById("appointmentCount").innerText = list.length;

  } catch (err) {
    table.innerHTML = `<tr><td colspan="11" class="empty-row">Could not load appointments.</td></tr>`;
    if (notifications) notifications.innerHTML = "";
    console.error("Failed to load appointments:", err);
  }
}

function rescheduleAppointment(doctorId) {
  if (doctorId) {
    localStorage.setItem("preferred_doctor_id", String(doctorId));
  }
  window.location.href = "../index.html";
}

function bookAnotherDoctor() {
  localStorage.removeItem("preferred_doctor_id");
  window.location.href = "../index.html";
}

/* ── Load medical records ── */
async function loadRecords() {
  const patientId = localStorage.getItem("patient_id");
  const table     = document.getElementById("recordsTable");

  if (!patientId) {
    table.innerHTML = `<tr><td colspan="3" class="empty-row">Not logged in.</td></tr>`;
    return;
  }

  try {
    const res  = await fetch(`${BACKEND}/patient/records?patient_id=${patientId}`);
    const data = await res.json();
    const list = data.records || data;

    table.innerHTML = "";

    if (!list || !list.length) {
      table.innerHTML = `<tr><td colspan="3" class="empty-row">No records found.</td></tr>`;
      return;
    }

    list.forEach(r => {
      table.innerHTML += `
        <tr>
          <td>${r.doctor || r.doctor_name || "—"}</td>
          <td>${r.diagnosis || "—"}</td>
          <td>${r.date || "—"}</td>
        </tr>
      `;
    });

    document.getElementById("reportCount").innerText = list.length;

  } catch (err) {
    table.innerHTML = `<tr><td colspan="3" class="empty-row">No records available.</td></tr>`;
    console.error("Failed to load records:", err);
  }
}

/* ── Load dashboard stats ── */
async function loadDashboardStats() {
  const patientId = localStorage.getItem("patient_id");
  
  if (!patientId) return;
  
  try {
    // Get unique doctors from appointments
    const appointmentsRes = await fetch(`${BACKEND}/patient/appointments?patient_id=${patientId}`);
    const appointmentsData = await appointmentsRes.json();
    const appointments = appointmentsData.appointments || appointmentsData;
    
    // Count unique doctors
    const uniqueDoctors = new Set();
    if (appointments && appointments.length) {
      appointments.forEach(a => {
        if (a.doctor || a.doctor_name) {
          uniqueDoctors.add(a.doctor || a.doctor_name);
        }
      });
    }
    document.getElementById("doctorCount").innerText = uniqueDoctors.size || "0";
    
  } catch (err) {
    console.error("Failed to load stats:", err);
  }
}

/* ── Logout ── */
function logout() {
  if (confirm("Are you sure you want to logout?")) {
    localStorage.clear();
    window.location.href = "../pages/login.html";
  }
}

/* ── Rating Modal Functions ── */
let currentRatingApptId = null;
let currentRating = 0;

function openRating(apptId, doctorName) {
  currentRatingApptId = apptId;
  currentRating = 0;
  
  let modal = document.getElementById('ratingModal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'ratingModal';
    modal.className = 'modal';
    modal.innerHTML = `
      <div class="modal-content">
        <h3>Rate Dr. <span id="ratingDoctorName"></span></h3>
        <div id="stars" class="rating-stars">
          <span onclick="setRating(1)">★</span>
          <span onclick="setRating(2)">★</span>
          <span onclick="setRating(3)">★</span>
          <span onclick="setRating(4)">★</span>
          <span onclick="setRating(5)">★</span>
        </div>
        <p style="text-align:center; color:#a0aec0; margin-bottom:15px">Tap a star to rate</p>
        <div id="reviewBox" style="display:none; margin-bottom:15px;">
          <p style="color:#ef9a9a; font-size:13px; margin-bottom:8px;">⚠️ We're sorry to hear that. Please tell us what went wrong:</p>
          <textarea id="reviewText" placeholder="Describe your experience..." style="
            width:100%; min-height:90px; padding:10px 12px;
            background:rgba(255,255,255,0.05); border:1px solid rgba(239,83,80,0.4);
            border-radius:10px; color:#e2e8f0; font-size:13px; font-family:inherit;
            resize:vertical; outline:none; box-sizing:border-box;
          "></textarea>
        </div>
        <div class="modal-buttons">
          <button onclick="submitRating()" class="btn-submit">Submit Rating</button>
          <button onclick="closeRating()" class="btn-cancel">Cancel</button>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
  }
  
  document.getElementById('ratingDoctorName').textContent = doctorName;
  document.getElementById('reviewBox').style.display = 'none';
  if (document.getElementById('reviewText')) document.getElementById('reviewText').value = '';
  highlightStars(0);
  modal.style.display = 'flex';
}

function closeRating() {
  const modal = document.getElementById('ratingModal');
  if (modal) modal.style.display = 'none';
}

function setRating(val) {
  currentRating = val;
  highlightStars(val);
  const reviewBox = document.getElementById('reviewBox');
  if (reviewBox) reviewBox.style.display = val <= 3 ? 'block' : 'none';
}

function highlightStars(val) {
  const stars = document.querySelectorAll('#stars span');
  stars.forEach((s, i) => {
    s.style.color = i < val ? '#f5a623' : '#555';
    s.style.transform = i < val ? 'scale(1.2)' : 'scale(1)';
  });
}

async function submitRating() {
  if (currentRating === 0) {
    alert('Please select a star rating.');
    return;
  }

  const review = (currentRating <= 3 && document.getElementById('reviewText'))
    ? document.getElementById('reviewText').value.trim()
    : '';

  try {
    const response = await fetch(`${BACKEND}/patient/rate-appointment`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        appointment_id: currentRatingApptId,
        rating: currentRating,
        review: review
      })
    });
    
    const data = await response.json();
    if (data.success) {
      alert('Thank you! Your rating has been submitted.');
      closeRating();
      loadAppointments();
    } else {
      alert(data.message || 'Failed to submit rating.');
    }
  } catch(e) {
    console.error("Rating error:", e);
    alert('Could not submit rating. Please try again later.');
  }
}

/* ── Report Upload ── */
function handleFileSelect(input) {
  const file = input.files[0];
  const content = document.getElementById('dropContent');
  if (file) {
    content.classList.add('has-file');
    content.innerHTML = `<i class="fa fa-file-alt"></i><span>${file.name}</span><small>${(file.size/1024).toFixed(1)} KB</small>`;
  }
}

// Drag-and-drop highlight
document.addEventListener('DOMContentLoaded', () => {
  const zone = document.getElementById('dropZone');
  if (zone) {
    zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragover'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
    zone.addEventListener('drop', e => { e.preventDefault(); zone.classList.remove('dragover'); });
  }
});

async function uploadReport() {
  const patientId  = localStorage.getItem('patient_id');
  const reportType = document.getElementById('reportType').value;
  const fileInput  = document.getElementById('reportFile');
  const msgEl      = document.getElementById('uploadMsg');
  const btn        = document.querySelector('.upload-btn');

  msgEl.className = 'upload-msg';
  msgEl.textContent = '';

  if (!reportType) { msgEl.className = 'upload-msg error'; msgEl.textContent = 'Please select a report type.'; return; }
  if (!fileInput.files[0]) { msgEl.className = 'upload-msg error'; msgEl.textContent = 'Please choose a file.'; return; }

  const file = fileInput.files[0];
  if (file.size > 5 * 1024 * 1024) { msgEl.className = 'upload-msg error'; msgEl.textContent = 'File too large. Max 5MB.'; return; }

  const formData = new FormData();
  formData.append('patient_id', patientId);
  formData.append('report_type', reportType);
  formData.append('file', file);

  btn.disabled = true;
  btn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Uploading…';

  try {
    const res  = await fetch(`${BACKEND}/patient/upload-report`, { method: 'POST', body: formData });
    const data = await res.json();

    if (data.success) {
      msgEl.className = 'upload-msg success';
      msgEl.textContent = '✓ Report uploaded successfully!';
      fileInput.value = '';
      document.getElementById('reportType').value = '';
      document.getElementById('dropContent').classList.remove('has-file');
      document.getElementById('dropContent').innerHTML = `
        <i class="fa fa-cloud-upload-alt"></i>
        <span>Drop file here or <u>browse</u></span>
        <small>PDF, JPG, PNG — max 5MB</small>`;
      loadUploadedReports();
    } else {
      msgEl.className = 'upload-msg error';
      msgEl.textContent = data.message || 'Upload failed.';
    }
  } catch(e) {
    msgEl.className = 'upload-msg error';
    msgEl.textContent = 'Could not connect to server.';
  }

  btn.disabled = false;
  btn.innerHTML = '<i class="fa fa-upload"></i> Upload Report';
}

async function loadUploadedReports() {
  const patientId = localStorage.getItem('patient_id');
  const tbody = document.getElementById('uploadsTableBody');
  if (!tbody) return;

  try {
    const res  = await fetch(`${BACKEND}/patient/reports?patient_id=${patientId}`);
    const data = await res.json();
    const list = data.reports || [];

    tbody.innerHTML = '';
    if (!list.length) {
      tbody.innerHTML = `<tr><td colspan="4" class="empty-row">No uploaded reports yet.</td></tr>`;
      return;
    }

    list.forEach(r => {
      tbody.innerHTML += `
        <tr>
          <td><span class="badge-type">${esc(r.report_type)}</span></td>
          <td>${esc(r.filename)}</td>
          <td>${esc(r.uploaded_at ? r.uploaded_at.split('T')[0] : '—')}</td>
          <td><a class="view-link" href="${BACKEND}/patient/report-file/${r.id}" target="_blank">
            <i class="fa fa-eye"></i> View
          </a></td>
          <td><button class="delete-report-btn" onclick="deleteReport(${r.id})">
            <i class="fa fa-trash"></i>
          </button></td>
        </tr>`;
    });

    // update stat card
    const el = document.getElementById('reportCount');
    if (el) el.textContent = list.length;

  } catch(e) {
    tbody.innerHTML = `<tr><td colspan="4" class="empty-row">Could not load reports.</td></tr>`;
  }
}

async function deleteReport(reportId) {
  if (!confirm('Delete this report? This cannot be undone.')) return;
  try {
    const res  = await fetch(`${BACKEND}/patient/report/${reportId}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.success) loadUploadedReports();
    else alert(data.message || 'Could not delete report.');
  } catch(e) {
    alert('Could not connect to server.');
  }
}

/* ── THEME ── */
function toggleTheme() {
  const isLight = document.body.classList.toggle('light-theme');
  localStorage.setItem('patientTheme', isLight ? 'light' : 'dark');
  const btn = document.getElementById('themeToggleBtn');
  if (btn) btn.textContent = isLight ? '🌙' : '☀️';
}

(function initTheme() {
  const saved = localStorage.getItem('patientTheme') || 'dark';
  const isLight = saved === 'light';
  document.body.classList.toggle('light-theme', isLight);
  const btn = document.getElementById('themeToggleBtn');
  if (btn) btn.textContent = isLight ? '🌙' : '☀️';
})();

/* ── Initialize everything on page load ── */
async function loadPatientAnnouncements() {
  const patientId = localStorage.getItem('patient_id');
  const box = document.getElementById('announcementBanners');
  if (!patientId || !box) return;
  try {
    const res = await fetch(`${BACKEND}/patient/announcements?patient_id=${patientId}`);
    const data = await res.json();
    const list = data.announcements || [];
    const unread = list.filter(a => !a.is_read);
    box.innerHTML = unread.slice(0, 3).map(a => `
      <div class="announcement-banner" data-id="${a.id}">
        <h4>${esc(a.title)}</h4>
        <p>${esc(a.message)}</p>
      </div>`).join('');
    unread.forEach(a => {
      fetch(`${BACKEND}/patient/announcements/${a.id}/read?patient_id=${patientId}`, { method: 'POST' }).catch(() => {});
    });
  } catch (_) {}
}

document.addEventListener("DOMContentLoaded", () => {
  loadAppointments();
  loadRecords();
  loadDashboardStats();
  loadUploadedReports();
  loadPatientAnnouncements();
  if (window.initPatientOnboarding) initPatientOnboarding();
});

/* ── Make functions global for HTML onclick ── */
window.showSection = showSection;
window.logout = logout;
window.openRating = openRating;
window.closeRating = closeRating;
window.setRating = setRating;
window.submitRating = submitRating;
window.toggleTheme = toggleTheme;
window.uploadReport = uploadReport;
window.handleFileSelect = handleFileSelect;
window.deleteReport = deleteReport;
window.rescheduleAppointment = rescheduleAppointment;
window.bookAnotherDoctor = bookAnotherDoctor;

/* ── MESSAGING ── */
let activeChatDoctorId = null;
let activeChatDoctorName = null;
let messagesPollTimer = null;

async function loadConversations() {
  const patientId = localStorage.getItem("patient_id");
  if (!patientId) return;

  try {
    const res = await fetch(`${BACKEND}/patient/conversations?patient_id=${patientId}`);
    const data = await res.json();
    const list = data.conversations || [];

    const container = document.getElementById("conversationsList");
    if (!list.length) {
      container.innerHTML = '<div class="conv-empty">No conversations yet.<br><small>Conversations start after a doctor messages you.</small></div>';
      return;
    }

    let totalUnread = 0;
    container.innerHTML = list.map(c => {
      totalUnread += c.unread_count || 0;
      const unreadHtml = c.unread_count > 0
        ? `<span class="conv-unread">${c.unread_count}</span>` : '';
      const isActive = c.doctor_id === activeChatDoctorId ? ' active' : '';
      return `
        <div class="conversation-item${isActive}" onclick="openPatientChat(${c.doctor_id}, '${esc(c.doctor_name)}')">
          <div class="conv-name">👨‍⚕️ ${esc(c.doctor_name)} ${unreadHtml}</div>
          <div class="conv-last">${esc(c.last_message || 'No messages yet')}</div>
        </div>`;
    }).join('');

    // Update sidebar badge
    const badge = document.getElementById("patientUnreadBadge");
    if (badge) {
      badge.textContent = totalUnread || '';
      badge.style.display = totalUnread > 0 ? 'inline' : 'none';
    }
  } catch (e) {
    console.error("loadConversations error:", e);
  }
}

async function openPatientChat(doctorId, doctorName) {
  activeChatDoctorId = doctorId;
  activeChatDoctorName = doctorName;

  document.getElementById("chatHeader").textContent = `👨‍⚕️ ${doctorName}`;
  document.getElementById("chatInputBar").style.display = "flex";

  // Mark as read
  const patientId = localStorage.getItem("patient_id");
  await fetch(`${BACKEND}/patient/mark-read`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ patient_id: parseInt(patientId), doctor_id: doctorId })
  }).catch(() => {});

  await loadPatientMessages();
  loadConversations(); // refresh unread counts

  // Highlight active conversation
  document.querySelectorAll(".conversation-item").forEach(el => el.classList.remove("active"));
  event && event.currentTarget && event.currentTarget.classList.add("active");
}

async function loadPatientMessages() {
  const patientId = localStorage.getItem("patient_id");
  if (!patientId || activeChatDoctorId === null) return;

  try {
    const res = await fetch(`${BACKEND}/patient/messages?patient_id=${patientId}&doctor_id=${activeChatDoctorId}`);
    const data = await res.json();
    const msgs = data.messages || [];

    const container = document.getElementById("chatMessages");
    if (!msgs.length) {
      container.innerHTML = '<div style="text-align:center; color:var(--muted); padding:20px; font-size:13px;">No messages yet. Say hello!</div>';
      return;
    }

    container.innerHTML = msgs.map(m => {
      const isSent = m.sender_role === 'patient';
      const time = m.created_at ? new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';
      return `
        <div class="message-bubble ${isSent ? 'message-sent' : 'message-received'}">
          ${esc(m.message_text)}
          <div class="message-time">${time}</div>
        </div>`;
    }).join('');

    // Auto-scroll to bottom
    container.scrollTop = container.scrollHeight;
  } catch (e) {
    console.error("loadPatientMessages error:", e);
  }
}

async function sendPatientMessage() {
  const patientId = localStorage.getItem("patient_id");
  const input = document.getElementById("messageInput");
  const text = input.value.trim();

  if (!text || activeChatDoctorId === null) return;

  input.value = '';
  try {
    await fetch(`${BACKEND}/patient/send-message`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        patient_id: parseInt(patientId),
        doctor_id: activeChatDoctorId,
        message: text
      })
    });
    await loadPatientMessages();
    loadConversations();
  } catch (e) {
    console.error("sendPatientMessage error:", e);
  }
}

function pollMessages() {
  // Replaced by WebSocket
}

let ws = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;

async function setupWebSocket() {
  const patientId = localStorage.getItem("patient_id");
  if (!patientId) return;

  try {
    const res = await fetch(`${BACKEND}/generate-ws-token?user_type=patient&user_id=${patientId}`);
    const data = await res.json();
    if (!data.token) throw new Error("No token received");

    // Connect to WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/patient/${patientId}?token=${data.token}`;
    
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log("WebSocket connected.");
      reconnectAttempts = 0; // Reset attempts on successful connection
      removeOfflineBanner();
    };

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === "new_message") {
          loadConversations();
          if (activeChatDoctorId !== null) loadPatientMessages();
        } else if (payload.type === "new_alert") {
          fetchAlerts();
        } else if (payload.type === "announcement") {
          loadPatientAnnouncements();
          if (typeof Notification !== 'undefined' && Notification.permission === 'granted') {
            new Notification(payload.title || 'SwasthSeva', { body: payload.message || '' });
          }
        } else if (payload.type === "ping") {
          ws.send("pong");
        }
      } catch(e) {}
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected.");
      attemptReconnect();
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

  } catch (err) {
    console.error("Failed to setup WebSocket:", err);
    attemptReconnect();
  }
}

function attemptReconnect() {
  if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
    showOfflineBanner();
    // Fallback to polling
    setInterval(() => {
      loadConversations();
      if (activeChatDoctorId !== null) loadPatientMessages();
      fetchAlerts();
    }, 5000);
    return;
  }
  
  const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 10000); // 1s, 2s, 4s, 8s, 10s
  reconnectAttempts++;
  console.log(`Reconnecting in ${delay}ms... (Attempt ${reconnectAttempts})`);
  setTimeout(setupWebSocket, delay);
}

function showOfflineBanner() {
  let banner = document.getElementById("offlineBanner");
  if (!banner) {
    banner = document.createElement("div");
    banner.id = "offlineBanner";
    banner.style.cssText = "position:fixed;top:0;left:0;width:100%;background:#ef5350;color:white;text-align:center;padding:10px;z-index:9999;font-weight:bold;";
    banner.textContent = "Connection Lost - Offline. Falling back to basic mode.";
    document.body.appendChild(banner);
  }
}

function removeOfflineBanner() {
  const banner = document.getElementById("offlineBanner");
  if (banner) banner.remove();
}

/* ── Override showSection to load conversations when messages tab opened ── */
const _origShowSection = window.showSection;
window.showSection = function(section, liEl) {
  _origShowSection(section, liEl);
  if (section === 'messages') loadConversations();
};

/* ── Make messaging functions global ── */
window.showSection = window.showSection;
window.openPatientChat = openPatientChat;
window.sendPatientMessage = sendPatientMessage;
window.loadConversations = loadConversations;

/* ── Start polling on load ── */
document.addEventListener("DOMContentLoaded", () => {
  loadConversations();
  fetchAlerts();
  setupWebSocket();
});
function jumpToDoctorChat(doctorId, doctorName) {
  showSection('messages', document.querySelector('.sidebar ul li:nth-child(4)'));
  openPatientChat(doctorId, doctorName);
}

function triggerSOS(doctorId, doctorName) {
  if (confirm(`🚨 TRIGGER EMERGENCY SOS TO DR. ${doctorName.toUpperCase()}?\n\nThis will notify the doctor and hospital emergency staff.`)) {
    alert(`SOS Sent to Dr. ${doctorName}. Help is on the way.`);
    // Here we would call a backend SOS API
  }
}

window.jumpToDoctorChat = jumpToDoctorChat;
window.triggerSOS = triggerSOS;

/* SOS POLLING */
let activeAlertId = null;

async function fetchAlerts() {
  const patientId = localStorage.getItem("patient_id");
  if (!patientId) return;

  try {
    const res = await fetch(`${BACKEND}/patient/active-alerts?patient_id=${patientId}`);
    const data = await res.json();
    const alerts = data.alerts || [];

    if (alerts.length > 0) {
      const alert = alerts[0];
      activeAlertId = alert.id;
      document.getElementById("sosMessage").textContent = `Alert raised by Dr. ${alert.doctor_name}`;
      document.getElementById("sosOverlay").classList.remove("hidden");
    }
  } catch (err) {
    console.error("Alert polling failed:", err);
  }
}

function dismissSOS() {
  console.log("Dismissing SOS...");
  const overlay = document.getElementById("sosOverlay");
  if (overlay) {
    overlay.style.display = "none";
    overlay.classList.add("hidden");
  }

  if (activeAlertId) {
    const aid = activeAlertId;
    activeAlertId = null;
    fetch(`${BACKEND}/patient/dismiss-alert/${aid}`, { 
      method: "POST",
      headers: { "Content-Type": "application/json" }
    }).catch(e => console.error("Server dismiss failed", e));
  }
}

// Ensure clicking ANY part of the overlay works
document.addEventListener('DOMContentLoaded', () => {
  const overlay = document.getElementById("sosOverlay");
  if (overlay) {
    overlay.addEventListener('click', dismissSOS);
  }
});

window.dismissSOS = dismissSOS;
window.fetchAlerts = fetchAlerts;
