const API = window.location.origin;

/* ── XSS helper ── */
function esc(str) {
  if (str === null || str === undefined) return '—';
  return String(str).replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
}

/* SWITCH */
function showSection(section, element) {
  document.querySelectorAll(".section").forEach(s => {
    s.classList.add("hidden");
  });
  const targetSection = document.getElementById(section);
  if (targetSection) targetSection.classList.remove("hidden");

  // Sync title
  const titleMap = {
    'dashboard': 'Dashboard',
    'appointments': 'Appointments',
    'prescription': 'Prescription',
    'ratings': 'My Ratings',
    'patients': 'My Patients',
    'messages': 'Messages'
  };
  document.getElementById('currentPageTitle').textContent = titleMap[section] || 'Dashboard';

  if (section === 'ratings') loadRatings();
  if (section === 'patients') loadPatients();
  if (section === 'appointments') loadAppointments();

  // Highlight logic for BOTH sidebar and mobile nav
  document.querySelectorAll(".sidebar ul li, .mobile-bottom-nav a").forEach(l => {
    l.classList.remove("active");
    // If this link's onclick contains the section name, mark it active
    const onclickStr = l.getAttribute('onclick') || "";
    if (onclickStr.includes(`'${section}'`)) {
      l.classList.add("active");
    }
  });

  // Ensure we scroll to top when changing sections
  window.scrollTo(0,0);
}

async function loadDoctor() {
  try {
    const doctorId = localStorage.getItem("doctor_id");
    const res  = await fetch(`${API}/doctor/dashboard?doctor_id=${doctorId}`);
    const data = await res.json();

    document.getElementById('profileName').textContent  = data.name || '—';
    document.getElementById('profileSpec').textContent  = data.specialization || data.department || '—';
    document.getElementById('profilePhone').textContent = data.phone || '—';
    document.getElementById('profileEmail').textContent = data.email || '—';
    document.getElementById('profileDays').textContent  = data.available_days || '—';
    document.getElementById('profileQual').textContent  = data.qualification || '—';
    document.getElementById('profileRegion').textContent = data.region || '—';

    document.getElementById('statToday').textContent    = data.appointments_today ?? '—';
    document.getElementById('statPatients').textContent = data.total_patients ?? '—';

    const rating = data.rating || 0;
    document.getElementById('statRating').innerHTML =
      `${Number(rating).toFixed(1)} <span style="font-size:16px; color:#f5a623;">${'★'.repeat(Math.round(rating))}${'☆'.repeat(5 - Math.round(rating))}</span>`;

    const avatar = document.getElementById('profileAvatar');
    if (avatar && data.name) avatar.innerHTML = `<span>${data.name.charAt(0).toUpperCase()}</span>`;

    const idBadge = document.getElementById('profileIdBadge');
    if (idBadge) idBadge.textContent = `ID: ${doctorId}`;

  } catch(e) {
    console.log("Error loading doctor:", e);
  }
}

async function loadAppointments(){
    try {
        const doctorId = localStorage.getItem("doctor_id");
        const res = await fetch(`${API}/doctor/appointments?doctor_id=${doctorId}`);
        const data = await res.json();

        allAppointments = data;
        renderCalendar();
        populateAppointmentTable(data);

    } catch(e) {
        console.log("Error loading appointments:", e);
    }
}

/* STARS */
function renderStars(rating){
  let stars = "";
  for(let i=1;i<=5;i++){
    stars += `<i class="fa fa-star" style="color:${i<=rating?'gold':'gray'}"></i>`;
  }
  return stars;
}

function savePrescription() {
  const patient  = document.getElementById('pname').value.trim();
  const medicine = document.getElementById('medicine').value.trim();
  const dosage   = document.getElementById('dosage').value.trim();

  if (!patient || !medicine || !dosage) {
    alert('Please fill in all fields.');
    return;
  }

  const doctorName = localStorage.getItem('name') || 'Doctor';
  const date       = new Date().toLocaleDateString('en-IN', {
    day: '2-digit', month: 'long', year: 'numeric'
  });

  const win = window.open('', '_blank');
  win.document.write(`
    <!DOCTYPE html>
    <html>
    <head>
      <title>Prescription</title>
      <style>
        body { font-family: 'Segoe UI', sans-serif; padding: 40px; color: #1a2744; }
        .header { text-align: center; border-bottom: 2px solid #1a3a5c; padding-bottom: 16px; margin-bottom: 24px; }
        .header h1 { color: #1a3a5c; font-size: 24px; margin: 0; }
        .header p  { color: #555; margin: 4px 0; font-size: 14px; }
        .section   { margin-bottom: 20px; }
        .label     { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #888; margin-bottom: 4px; }
        .value     { font-size: 16px; font-weight: 600; color: #1a2744; }
        .rx        { font-size: 40px; color: #1a3a5c; font-weight: 700; margin-bottom: 8px; }
        .medicine-box {
          background: #f0f4f8;
          border-left: 4px solid #1a3a5c;
          padding: 16px 20px;
          border-radius: 4px;
          margin-top: 8px;
        }
        .footer { margin-top: 48px; border-top: 1px solid #ccc; padding-top: 16px; display: flex; justify-content: space-between; font-size: 13px; color: #888; }
        .signature { text-align: right; }
        .signature strong { display: block; color: #1a2744; font-size: 15px; }
      </style>
    </head>
    <body>
      <div class="header">
        <h1>SwasthSeva</h1>
        <p>Government Hospital System — Digital Prescription</p>
        <p>Date: ${date}</p>
      </div>

      <div class="section">
        <div class="label">Patient Name</div>
        <div class="value">${patient}</div>
      </div>

      <div class="section">
        <div class="rx">℞</div>
        <div class="label">Medicine</div>
        <div class="medicine-box">
          <div class="value">${medicine}</div>
          <div style="margin-top:8px;">
            <span class="label">Dosage: </span>
            <span style="font-size:14px; color:#333;">${dosage}</span>
          </div>
        </div>
      </div>

      <div class="footer">
        <div>This is a digitally generated prescription.</div>
        <div class="signature">
          <strong>Dr. ${doctorName}</strong>
          SwasthSeva
        </div>
      </div>

      <script>
        window.onload = function() { window.print(); }
      <\/script>
    </body>
    </html>
  `);
  win.document.close();

  document.getElementById('pname').value    = '';
  document.getElementById('medicine').value = '';
  document.getElementById('dosage').value   = '';
}

/* LOGOUT */
function logout(){
  localStorage.clear();
  window.location.href = "../pages/login.html";
}

/* CALENDAR */
let calDate = new Date();
let allAppointments = [];
let selectedDate = null;

function renderCalendar() {
  const year  = calDate.getFullYear();
  const month = calDate.getMonth();

  document.getElementById('calMonthLabel').textContent =
    calDate.toLocaleDateString('en-IN', { month: 'long', year: 'numeric' });

  const grid = document.getElementById('calGrid');
  grid.innerHTML = '';

  ['Su','Mo','Tu','We','Th','Fr','Sa'].forEach(d => {
    const h = document.createElement('div');
    h.className = 'cal-day-header';
    h.textContent = d;
    grid.appendChild(h);
  });

  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  for (let i = 0; i < firstDay; i++) {
    grid.appendChild(Object.assign(document.createElement('div'), { className: 'cal-cell empty' }));
  }

  for (let d = 1; d <= daysInMonth; d++) {
    const cell = document.createElement('div');
    cell.className = 'cal-cell';
    cell.textContent = d;

    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;

    const hasAppt = allAppointments.some(a => a.date === dateStr);
    if (hasAppt) cell.classList.add('has-appt');

    if (selectedDate === dateStr) cell.classList.add('selected');

    cell.onclick = () => selectDate(dateStr);
    grid.appendChild(cell);
  }
}

function selectDate(dateStr) {
  selectedDate = dateStr;
  renderCalendar();

  const filtered = allAppointments.filter(a => a.date === dateStr);
  const label = document.getElementById('calSelectedLabel');
  const table = document.getElementById('appointmentTable');

  label.textContent = filtered.length
    ? `Showing ${filtered.length} appointment(s) for ${dateStr}`
    : `No appointments on ${dateStr}`;

  table.innerHTML = '';
  if (!filtered.length) {
    table.innerHTML = "<tr><td colspan='9'>No appointments on this date.</td></tr>";
    return;
  }
  filtered.forEach(a => {
    const chatBtn = `<button class="btn-chat" onclick="jumpToPatientChat(${a.patient_id}, '${esc(a.patient_name)}')"><i class="fa fa-comments"></i></button>`;
    const historyBtn = `<button class="btn-history-mini" title="Medical History" onclick="viewPatientHistory(${a.patient_id}, '${esc(a.patient_name)}')"><i class="fa fa-book-medical"></i></button>`;
    
    table.innerHTML += `
      <tr>
        <td>${a.id}</td>
        <td>${a.patient_name}</td>
        <td>${a.date}</td>
        <td>${a.time}</td>
        <td>${a.status}</td>
        <td>${esc(a.reason)}</td>
        <td class="action-cell">
          ${chatBtn}
          ${historyBtn}
        </td>
        <td><button class="btn-cancel-appt" onclick="cancelAppointment(${a.id})">Cancel</button></td>
        <td><button class="btn-meet" onclick="createMeet(${a.id}, ${a.patient_id})"><i class="fa fa-video"></i></button></td>
      </tr>`;
  });
}

function changeMonth(dir) {
  calDate.setMonth(calDate.getMonth() + dir);
  selectedDate = null;
  renderCalendar();
  populateAppointmentTable(allAppointments);
  document.getElementById('calSelectedLabel').textContent = '';
}

function populateAppointmentTable(data) {
  const table = document.getElementById('appointmentTable');
  table.innerHTML = '';
  if (!data.length) {
    table.innerHTML = "<tr><td colspan='9'>No appointments yet.</td></tr>";
    return;
  }
  data.forEach(a => {
    const status = a.status || 'Pending';
    const loweredStatus = status.toLowerCase();
    const reason = a.cancellation_reason || a.reason || '—';
    const canCancel = ['booked', 'scheduled', 'confirmed', 'upcoming', 'pending'].includes(loweredStatus);
    const cancelBtn = canCancel
      ? `<button class="btn-cancel-appt" onclick="cancelAppointment(${a.id})">Cancel</button>`
      : '';
    const chatBtn = `<button class="btn-chat" onclick="jumpToPatientChat(${a.patient_id}, '${esc(a.patient_name)}')"><i class="fa fa-comments"></i></button>`;
    const historyBtn = `<button class="btn-history-mini" title="Medical History" onclick="viewPatientHistory(${a.patient_id}, '${esc(a.patient_name)}')"><i class="fa fa-book-medical"></i></button>`;
    const meetBtn = `<button class="btn-meet" onclick="createMeet(${a.id}, ${a.patient_id || 0})"><i class="fa fa-video"></i></button>`;
    const sosBtn = `<button class="btn-sos-mini" title="EMERGENCY" onclick="triggerSOS(${a.patient_id}, '${esc(a.patient_name)}')"><i class="fa fa-bell"></i> SOS</button>`;

    table.innerHTML += `
      <tr>
        <td>${a.id}</td>
        <td>${a.patient_name} ${sosBtn}</td>
        <td>${a.date}</td>
        <td>${a.time}</td>
        <td>${status}</td>
        <td>${esc(reason)}</td>
        <td class="action-cell">
          ${chatBtn}
          ${historyBtn}
          ${meetBtn}
        </td>
        <td>${cancelBtn}</td>
        <td>—</td>
      </tr>`;
  });
}

async function createMeet(appointmentId, patientId) {
  const scheduledTime = prompt('Enter meeting time (e.g. Today 3:00 PM):');
  if (!scheduledTime) return;

  const doctorId = localStorage.getItem('doctor_id');
  try {
    const res = await fetch(`${API}/doctor/create-meet`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        doctor_id: parseInt(doctorId),
        patient_id: patientId,
        appointment_id: appointmentId,
        scheduled_time: scheduledTime
      })
    });
    const data = await res.json();
    if (data.success) {
      alert(`Meet link created and sent to patient!\n\n${data.meet_link}`);
      window.open(data.meet_link, '_blank');
    } else {
      alert(data.message || 'Could not create meet link.');
    }
  } catch (e) {
    alert('Could not connect to server.');
  }
}

async function cancelAppointment(appointmentId) {
  const doctorId = localStorage.getItem('doctor_id');
  const reason = prompt('Enter emergency reason for cancellation:');
  if (!reason || !reason.trim()) {
    return;
  }

  try {
    const res = await fetch(`${API}/doctor/appointments/${appointmentId}/cancel`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        doctor_id: Number(doctorId),
        cancellation_reason: reason.trim()
      })
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      alert(data.message || 'Could not cancel appointment.');
      return;
    }
    alert('Appointment cancelled. Patient has been notified.');
    await loadAppointments();
  } catch (e) {
    alert('Could not connect to server.');
  }
}

async function loadRatings() {
  const doctorId = localStorage.getItem('doctor_id');
  const tbody    = document.getElementById('ratingsTable');

  try {
    const res  = await fetch(`${API}/doctor/ratings?doctor_id=${doctorId}`);
    const data = await res.json();
    const list = data.ratings || [];

    if (list.length) {
      const avg = list.reduce((s, r) => s + r.rating, 0) / list.length;
      document.getElementById('avgScore').textContent     = avg.toFixed(1) + ' / 5';
      document.getElementById('totalReviews').textContent = list.length + ' reviews';
      document.getElementById('avgStars').textContent     = '★'.repeat(Math.round(avg)) + '☆'.repeat(5 - Math.round(avg));
    }

    tbody.innerHTML = '';
    if (!list.length) {
      tbody.innerHTML = `<tr><td colspan="4" class="empty-row">No ratings yet</td></tr>`;
      return;
    }

    list.forEach(r => {
      const isLow = r.rating <= 3;
      tbody.innerHTML += `
        <tr${isLow ? ' style="background:rgba(239,83,80,0.07);"' : ''}>
          <td>${esc(r.patient_name)}</td>
          <td>${'★'.repeat(r.rating)}${'☆'.repeat(5 - r.rating)}</td>
          <td>${r.review
            ? `<span style="color:${isLow ? '#ef9a9a' : '#a0aec0'}; font-style:italic;">"${esc(r.review)}"</span>`
            : '<span style="color:#4a5568;">—</span>'
          }</td>
          <td>${esc(r.date)}</td>
        </tr>`;
    });

  } catch(e) {
    if (tbody) tbody.innerHTML = `<tr><td colspan="4" class="empty-row">Could not load ratings</td></tr>`;
  }
}

async function loadPatients() {
  const doctorId = localStorage.getItem('doctor_id');
  const tbody    = document.getElementById('patientsTable');

  try {
    const res  = await fetch(`${API}/doctor/patients?doctor_id=${doctorId}`);
    const data = await res.json();

    tbody.innerHTML = '';
    const dropdown = document.getElementById('pname');
    if (dropdown) dropdown.innerHTML = '<option value="">Select Patient</option>';

    if (!data || !data.length) {
      tbody.innerHTML = `<tr><td colspan="6" class="empty-row">No patients found</td></tr>`;
      return;
    }

    data.forEach(p => {
      // Add to dropdown
      if (dropdown) {
        const opt = document.createElement('option');
        opt.value = p.name;
        opt.textContent = p.name;
        dropdown.appendChild(opt);
      }

      const sosBtn = `<button class="btn-sos-mini" onclick="triggerSOS(${p.patient_id}, '${esc(p.name)}')"><i class="fa fa-bell"></i> SOS</button>`;

      tbody.innerHTML += `
        <tr>
          <td>${esc(p.patient_id)}</td>
          <td>${esc(p.name)} ${sosBtn}</td>
          <td>${esc(p.age)}</td>
          <td>${esc(p.gender)}</td>
          <td>${esc(p.phone)}</td>
          <td class="action-cell">
            <button class="btn-chat" onclick="jumpToPatientChat(${p.patient_id}, '${esc(p.name)}')">
              <i class="fa fa-comments"></i> Message
            </button>
            <button class="btn-history" onclick="viewPatientHistory(${p.patient_id}, '${esc(p.name)}')">
              <i class="fa fa-book-medical"></i> History
            </button>
          </td>
        </tr>`;
    });

  } catch(e) {
    if (tbody) tbody.innerHTML = `<tr><td colspan="6" class="empty-row">Could not load patients</td></tr>`;
  }
}

/* THEME */
function toggleTheme() {
  const isLight = document.body.classList.toggle('light-theme');
  localStorage.setItem('doctorTheme', isLight ? 'light' : 'dark');
  const btn = document.getElementById('themeToggleBtn');
  if (btn) btn.textContent = isLight ? '🌙' : '☀️';
}

(function initTheme() {
  const saved = localStorage.getItem('doctorTheme') || 'dark';
  const isLight = saved === 'light';
  document.body.classList.toggle('light-theme', isLight);
  const btn = document.getElementById('themeToggleBtn');
  if (btn) btn.textContent = isLight ? '🌙' : '☀️';
})();

/* INIT */
loadDoctor();
loadAppointments();

/* ── MESSAGING ── */
let activeChatPatientId = null;
let activeChatPatientName = null;
let doctorMsgPollTimer = null;

function jumpToPatientChat(patientId, patientName) {
  showSection('messages', document.querySelector('.sidebar ul li:nth-child(6)')); // Messages is usually 6th item
  openDoctorChat(patientId, patientName);
}

async function loadDoctorConversations() {
  const doctorId = localStorage.getItem("doctor_id");
  if (!doctorId) return;

  try {
    const res = await fetch(`${API}/doctor/conversations?doctor_id=${doctorId}`);
    const data = await res.json();
    const list = data.conversations || [];

    const container = document.getElementById("conversationsList");
    if (!container) return;

    if (!list.length) {
      container.innerHTML = '<div class="conv-empty">No conversations yet.</div>';
      return;
    }

    let totalUnread = 0;
    container.innerHTML = list.map(c => {
      totalUnread += c.unread_count || 0;
      const unreadHtml = c.unread_count > 0
        ? `<span class="conv-unread">${c.unread_count}</span>` : '';
      const isActive = c.patient_id === activeChatPatientId ? ' active' : '';
      return `
        <div class="conversation-item${isActive}" onclick="openDoctorChat(${c.patient_id}, '${esc(c.patient_name)}')">
          <div class="conv-name">🧑‍⚕️ ${esc(c.patient_name)} ${unreadHtml}</div>
          <div class="conv-last">${esc(c.last_message || 'No messages yet')}</div>
        </div>`;
    }).join('');

    const badge = document.getElementById("doctorUnreadBadge");
    if (badge) {
      badge.textContent = totalUnread || '';
      badge.style.display = totalUnread > 0 ? 'inline' : 'none';
    }
  } catch (e) {
    console.error("loadDoctorConversations error:", e);
  }
}

async function openDoctorChat(patientId, patientName) {
  activeChatPatientId = patientId;
  activeChatPatientName = patientName;

  const header = document.getElementById("chatHeader");
  const inputBar = document.getElementById("chatInputBar");
  if (header) header.textContent = `🧑‍⚕️ ${patientName}`;
  if (inputBar) inputBar.style.display = "flex";

  const doctorId = localStorage.getItem("doctor_id");
  await fetch(`${API}/doctor/mark-read`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doctor_id: parseInt(doctorId), patient_id: patientId })
  }).catch(() => {});

  await loadDoctorMessages();
  loadDoctorConversations();
}

async function loadDoctorMessages() {
  const doctorId = localStorage.getItem("doctor_id");
  if (!doctorId || !activeChatPatientId) return;

  try {
    const res = await fetch(`${API}/doctor/messages?doctor_id=${doctorId}&patient_id=${activeChatPatientId}`);
    const data = await res.json();
    const msgs = data.messages || [];

    const container = document.getElementById("chatMessages");
    if (!container) return;

    if (!msgs.length) {
      container.innerHTML = '<div style="text-align:center; color:#94a3b8; padding:20px; font-size:13px;">No messages yet. Start the conversation!</div>';
      return;
    }

    container.innerHTML = msgs.map(m => {
      const isSent = m.sender_role === 'doctor';
      const time = m.created_at ? new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';
      return `
        <div class="message-bubble ${isSent ? 'message-sent' : 'message-received'}">
          ${esc(m.message_text)}
          <div class="message-time">${time}</div>
        </div>`;
    }).join('');

    container.scrollTop = container.scrollHeight;
  } catch (e) {
    console.error("loadDoctorMessages error:", e);
  }
}

async function sendDoctorMessage() {
  const doctorId = localStorage.getItem("doctor_id");
  const input = document.getElementById("messageInput");
  const text = input ? input.value.trim() : '';

  if (!text || !activeChatPatientId) return;
  input.value = '';

  try {
    await fetch(`${API}/doctor/send-message`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        doctor_id: parseInt(doctorId),
        patient_id: activeChatPatientId,
        message: text
      })
    });
    await loadDoctorMessages();
    loadDoctorConversations();
  } catch (e) {
    console.error("sendDoctorMessage error:", e);
  }
}

/* ── Extend showSection to load conversations when messages tab opened ── */
const _origDoctorShowSection = window.showSection || showSection;
window.showSection = function(section, element) {
  _origDoctorShowSection(section, element);
  if (section === 'messages') loadDoctorConversations();
};

/* ── Poll for new messages every 5s ── */
function startDoctorMsgPoll() {
  if (doctorMsgPollTimer) clearInterval(doctorMsgPollTimer);
  doctorMsgPollTimer = setInterval(() => {
    loadDoctorConversations();
    if (activeChatPatientId) loadDoctorMessages();
  }, 5000);
}

window.openDoctorChat = openDoctorChat;
window.sendDoctorMessage = sendDoctorMessage;
window.loadDoctorConversations = loadDoctorConversations;
window.jumpToPatientChat = jumpToPatientChat;

/* ── Init messaging on load ── */
document.addEventListener("DOMContentLoaded", () => {
  loadDoctorConversations();
  startDoctorMsgPoll();
});

async function viewPatientHistory(patientId, patientName) {
  const modal = document.getElementById('historyModal');
  const title = document.getElementById('historyModalTitle');
  const body  = document.getElementById('historyModalBody');
  
  title.textContent = `Medical History: ${patientName}`;
  body.innerHTML = '<div class="loading-spinner">Loading reports...</div>';
  modal.classList.add('show');

  try {
    const res = await fetch(`${API}/doctor/patient-reports/${patientId}`);
    const data = await res.json();
    const reports = data.reports || [];

    if (!reports.length) {
      body.innerHTML = `
        <div class="empty-history">
          <i class="fa fa-file-medical-alt" style="font-size: 2rem; color: #64748b; margin-bottom: 12px; display: block;"></i>
          <p>No medical reports found for this patient ID.</p>
          <button class="btn-history" onclick="viewPatientHistory(${patientId}, '${patientName}')" style="margin-top:12px;">
            <i class="fa fa-sync"></i> Retry Refresh
          </button>
        </div>`;
      return;
    }

    body.innerHTML = `
      <table class="history-table">
        <thead>
          <tr>
            <th>Type</th>
            <th>Filename</th>
            <th>Date</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          ${reports.map(r => `
            <tr>
              <td><span class="report-type-badge">${esc(r.report_type)}</span></td>
              <td>${esc(r.filename)}</td>
              <td>${r.uploaded_at ? r.uploaded_at.split(' ')[0] : '—'}</td>
              <td>
                <a href="${API}/patient/report-file/${r.id}" target="_blank" class="btn-view-file">
                  <i class="fa fa-eye"></i> View
                </a>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  } catch (e) {
    body.innerHTML = '<div class="error-msg">Failed to load reports.</div>';
  }
}

function closeHistoryModal() {
  document.getElementById('historyModal').classList.remove('show');
}

async function triggerSOS(patientId, patientName) {
  if (confirm(`🚨 TRIGGER EMERGENCY SOS FOR ${patientName.toUpperCase()}?\n\nThis will notify the patient and hospital emergency staff.`)) {
    try {
      const doctorId = localStorage.getItem("doctor_id");
      const res = await fetch(`${BACKEND}/doctor/trigger-sos`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ patient_id: patientId, doctor_id: doctorId })
      });
      const data = await res.json();
      if (data.success) {
        alert(`SOS Triggered for ${patientName}. Help is on the way.`);
      }
    } catch (err) {
      console.error("SOS failed:", err);
      alert("Failed to trigger SOS. Please contact the patient directly.");
    }
  }
}

window.viewPatientHistory = viewPatientHistory;
window.closeHistoryModal = closeHistoryModal;
window.triggerSOS = triggerSOS;
