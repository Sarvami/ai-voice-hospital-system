const BACKEND = "http://127.0.0.1:8000";

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

  if (!patientId) {
    table.innerHTML = `<tr><td colspan="7" class="empty-row">Not logged in.</td></tr>`;
    return;
  }

  try {
    const res  = await fetch(`${BACKEND}/patient/appointments?patient_id=${patientId}`);
    const data = await res.json();
    const list = data.appointments || data;

    table.innerHTML = "";

    if (!list || !list.length) {
      table.innerHTML = `<tr><td colspan="9" class="empty-row">No appointments found.</td></tr>`;
      return;
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
          <td>${actionHtml}</td>
        </tr>
      `;
    });

    document.getElementById("appointmentCount").innerText = list.length;

  } catch (err) {
    table.innerHTML = `<tr><td colspan="9" class="empty-row">Could not load appointments.</td></tr>`;
    console.error("Failed to load appointments:", err);
  }
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
document.addEventListener("DOMContentLoaded", () => {
  loadAppointments();
  loadRecords();
  loadDashboardStats();
  loadUploadedReports();
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
