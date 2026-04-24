const API = window.location.origin;

let allDoctors      = [];
let allAppointments = [];

/* ── XSS helper ── */
function esc(str) {
  if (str === null || str === undefined) return '—';
  return String(str).replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
}

const sectionTitles = {
  overview:     'Overview',
  patients:     'Patients',
  viewDoctors:  'Doctors — View',
  createDoctor: 'Doctors — Create',
  appointments: 'Appointments',
  nurses:       'Assign Nurses',
  leaves:       'Staff Leaves',
  ratings:      'Ratings & Reviews',
  voice:        'Voice Notes',
};

function showSection(section, liEl) {
  document.querySelectorAll('.section').forEach(s => s.classList.add('hidden'));
  document.getElementById(section).classList.remove('hidden');
  document.querySelectorAll('.sidebar li').forEach(l => l.classList.remove('active'));
  if (liEl) liEl.classList.add('active');
  document.getElementById('currentPageTitle').textContent = sectionTitles[section] || '';
  if (section === 'patients')     loadPatients();
  if (section === 'viewDoctors')  loadDoctors();
  if (section === 'appointments') loadAppointments();
  if (section === 'ratings')      loadRatings();
}

function toggleDoctorMenu(liEl) {
  const submenu = document.getElementById('doctorSubmenu');
  const arrow   = document.getElementById('doctorArrow');
  submenu.classList.toggle('hidden');
  arrow.classList.toggle('rotated');
  if (liEl) {
    document.querySelectorAll('.sidebar > ul > li').forEach(l => l.classList.remove('active'));
    liEl.classList.add('active');
  }
}

/* ── OVERVIEW ── */
async function loadOverview() {
  try {
    const res  = await fetch(`${API}/admin-api/overview`);
    const data = await res.json();
    document.getElementById('totalPatients').innerText     = data.patients     ?? 0;
    document.getElementById('totalDoctors').innerText      = data.doctors      ?? 0;
    document.getElementById('totalAppointments').innerText = data.appointments ?? 0;
  } catch(e) {
    console.log('Backend not connected');
  }
}

let allPatients = [];

async function loadPatients() {
  const table = document.getElementById('patientsTable');
  try {
    const res  = await fetch(`${API}/admin-api/patients`);
    const data = await res.json();
    allPatients = data;
    table.innerHTML = '';
    if (!data.length) {
      table.innerHTML = `<tr><td colspan="8" class="empty-row">No patients found</td></tr>`;
      return;
    }
    data.forEach(p => {
      table.innerHTML += `
        <tr>
          <td>${esc(p.patient_id)}</td>
          <td>${esc(p.name)}</td>
          <td>${esc(p.age)}</td>
          <td>${esc(p.gender)}</td>
          <td>${esc(p.phone)}</td>
          <td>${esc(p.email)}</td>
          <td>${esc(p.preferred_language)}</td>
          <td>
            <i class="fa-solid fa-pen-to-square edit-btn" title="Edit" onclick="openEditModal(${p.patient_id})"></i>
            <i class="fa-solid fa-paper-plane edit-btn" title="Message Patient" style="margin-left:10px; color:#69f0ae;" onclick="openMessageModal(${p.patient_id}, '${esc(p.name)}')"></i>
            <i class="fa-solid fa-folder-open edit-btn" title="View Reports" style="margin-left:10px; color:#38bdf8;" onclick="openReportsModal(${p.patient_id}, '${esc(p.name)}')"></i>
          </td>
        </tr>`;
    });
  } catch(e) {
    table.innerHTML = `<tr><td colspan="7" class="empty-row">Could not load</td></tr>`;
  }
}

function openEditModal(id) {
  const p = allPatients.find(item => item.patient_id === id);
  if (!p) return;
  
  document.getElementById('editPatientId').value = p.patient_id;
  document.getElementById('editPatientName').value = p.name;
  document.getElementById('editPatientAge').value = p.age;
  document.getElementById('editPatientGender').value = p.gender || 'Male';
  document.getElementById('editPatientPhone').value = p.phone;
  document.getElementById('editPatientEmail').value = p.email || '';
  document.getElementById('editPatientLang').value = p.preferred_language || 'en';
  
  document.getElementById('editPatientModal').classList.remove('hidden');
}

function closeEditModal() {
  document.getElementById('editPatientModal').classList.add('hidden');
}

async function savePatientEdit() {
  const patient_id = document.getElementById('editPatientId').value;
  const name = document.getElementById('editPatientName').value;
  const age = document.getElementById('editPatientAge').value;
  const gender = document.getElementById('editPatientGender').value;
  const phone = document.getElementById('editPatientPhone').value;
  const email = document.getElementById('editPatientEmail').value;
  const preferred_language = document.getElementById('editPatientLang').value;

  try {
    const res = await fetch(`${API}/admin-api/update-patient`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ patient_id: parseInt(patient_id), name, age: parseInt(age), gender, phone, email, preferred_language })
    });
    const result = await res.json();
    if (result.success) {
      closeEditModal();
      loadPatients(); // refresh data
    } else {
      alert("Update failed: " + result.message);
    }
  } catch(e) {
    alert("Error updating patient.");
  }
}

/* ── PATIENT REPORTS MODAL ── */
async function openReportsModal(patientId, patientName) {
  document.getElementById('reportsModalTitle').textContent = `Reports — ${patientName}`;
  const tbody = document.getElementById('reportsModalBody');
  tbody.innerHTML = `<tr><td colspan="4" class="empty-row">Loading…</td></tr>`;
  document.getElementById('patientReportsModal').classList.remove('hidden');

  try {
    const res  = await fetch(`${API}/patient/reports?patient_id=${patientId}`);
    const data = await res.json();
    const list = data.reports || [];

    tbody.innerHTML = '';
    if (!list.length) {
      tbody.innerHTML = `<tr><td colspan="4" class="empty-row">No reports uploaded by this patient.</td></tr>`;
      return;
    }
    list.forEach(r => {
      tbody.innerHTML += `
        <tr>
          <td><span class="hours-badge">${r.report_type}</span></td>
          <td>${r.filename}</td>
          <td>${r.uploaded_at ? r.uploaded_at.split('T')[0] : '—'}</td>
          <td><a href="${API}/patient/report-file/${r.id}" target="_blank"
              style="color:#38bdf8; text-decoration:none; font-size:13px;">
            <i class="fa fa-eye"></i> View
          </a></td>
        </tr>`;
    });
  } catch(e) {
    tbody.innerHTML = `<tr><td colspan="4" class="empty-row">Could not load reports.</td></tr>`;
  }
}

function closeReportsModal() {
  document.getElementById('patientReportsModal').classList.add('hidden');
}

/* ── MESSAGE PATIENT ── */
function openMessageModal(patientId, patientName) {
  document.getElementById('messagePatientId').value = patientId;
  document.getElementById('messageModalTitle').innerText = `Message ${patientName}`;
  document.getElementById('adminMessageText').value = '';
  document.getElementById('messageModal').classList.remove('hidden');
}

function closeMessageModal() {
  document.getElementById('messageModal').classList.add('hidden');
}

async function sendMessage() {
  const patientId = document.getElementById('messagePatientId').value;
  const message   = document.getElementById('adminMessageText').value.trim();

  if (!message) { alert("Please type a message."); return; }

  try {
    const res = await fetch(`${API}/admin-api/send-message`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        receiver_id:  parseInt(patientId),
        message_text: message
      }),
    });
    const data = await res.json();
    if (data.success) {
      alert("✓ Message sent to patient!");
      closeMessageModal();
    } else {
      alert("Error: " + data.message);
    }
  } catch(e) {
    alert("Could not connect to server.");
  }
}

/* ── DOCTORS ── */
async function loadDoctors() {
  const table = document.getElementById('doctorsTable');
  try {
    const res  = await fetch(`${API}/admin-api/doctors`);
    const data = await res.json();
    allDoctors = data;
    renderDoctors(allDoctors);
  } catch(e) {
    table.innerHTML = `<tr><td colspan="11" class="empty-row">Could not load</td></tr>`;
  }
}

function renderDoctors(list) {
  const table = document.getElementById('doctorsTable');
  table.innerHTML = '';
  if (!list.length) {
    table.innerHTML = `<tr><td colspan="11" class="empty-row">No doctors found</td></tr>`;
    return;
  }
  list.forEach(d => {
    const hours = d.available_hours || '8:00 AM - 8:00 PM';
    const isSpecial = hours !== '8:00 AM - 8:00 PM';
    const hoursBadge = isSpecial
      ? `<span class="hours-badge hours-special">${hours}</span>`
      : `<span class="hours-badge">${hours}</span>`;

    table.innerHTML += `
      <tr>
        <td>${d.doc_id || '—'}</td>
        <td>${d.name || '—'}</td>
        <td>${d.contact_phone || '—'}</td>
        <td>${d.email || '—'}</td>
        <td>${d.department || '—'}</td>
        <td>${d.qualification || '—'}</td>
        <td>${d.experience_years ?? '—'} yrs</td>
        <td>${d.available_days || '—'}</td>
        <td>${hoursBadge}</td>
        <td>${d.region || '—'}</td>
        <td>
            <i class="fa-solid fa-pen-to-square edit-btn" title="Edit Doctor" onclick="openEditDoctorModal(${d.doctor_id})"></i>
        </td>
      </tr>`;
  });
}

function openEditDoctorModal(id) {
    const d = allDoctors.find(item => item.doctor_id === id);
    if (!d) return;
    
    document.getElementById('editDoctorIdInternal').value = d.doctor_id;
    document.getElementById('editDoctorName').value = d.name;
    document.getElementById('editDoctorDept').value = d.department;
    document.getElementById('editDoctorRegion').value = d.region;
    document.getElementById('editDoctorQual').value = d.qualification;
    document.getElementById('editDoctorExp').value = d.experience_years;
    document.getElementById('editDoctorIdPublic').value = d.doc_id;
    document.getElementById('editDoctorPhone').value = d.contact_phone;
    document.getElementById('editDoctorEmail').value = d.email;
    document.getElementById('editDoctorDays').value = d.available_days;
    document.getElementById('editDoctorHours').value = d.available_hours || '8:00 AM - 8:00 PM';
    
    document.getElementById('editDoctorModal').classList.remove('hidden');
}

function closeEditDoctorModal() {
    document.getElementById('editDoctorModal').classList.add('hidden');
}

async function saveDoctorEdit() {
    const payload = {
        doctor_id: parseInt(document.getElementById('editDoctorIdInternal').value),
        name: document.getElementById('editDoctorName').value,
        department: document.getElementById('editDoctorDept').value,
        region: document.getElementById('editDoctorRegion').value,
        qualification: document.getElementById('editDoctorQual').value,
        experience_years: parseInt(document.getElementById('editDoctorExp').value),
        doc_id: document.getElementById('editDoctorIdPublic').value,
        contact_phone: document.getElementById('editDoctorPhone').value,
        email: document.getElementById('editDoctorEmail').value,
        available_days: document.getElementById('editDoctorDays').value,
        available_hours: document.getElementById('editDoctorHours').value
    };

    try {
        const res = await fetch(`${API}/admin-api/update-doctor`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await res.json();
        if (result.success) {
            closeEditDoctorModal();
            loadDoctors();
        } else {
            alert("Update failed: " + result.message);
        }
    } catch(e) {
        alert("Error updating doctor.");
    }
}

/* ── THEME TOGGLE ── */
function toggleTheme() {
  const isLight = document.body.classList.toggle('light-theme');
  if (isLight) {
    document.body.classList.remove('dark-theme');
    localStorage.setItem('adminTheme', 'light');
  } else {
    document.body.classList.add('dark-theme');
    localStorage.setItem('adminTheme', 'dark');
  }
  const btn = document.getElementById('themeToggleBtn');
  if (btn) btn.textContent = isLight ? '🌙' : '☀️';
}

// Initial theme check
(function initTheme() {
    const saved = localStorage.getItem('adminTheme') || 'dark';
    if (saved === 'light') {
        document.body.classList.add('light-theme');
        document.body.classList.remove('dark-theme');
        const btn = document.getElementById('themeToggleBtn');
        if (btn) btn.textContent = '🌙';
    } else {
        document.body.classList.add('dark-theme');
        document.body.classList.remove('light-theme');
        const btn = document.getElementById('themeToggleBtn');
        if (btn) btn.textContent = '☀️';
    }
})();

/* ── DEPARTMENT FILTER ── */
function filterDoctors() {
  const dept = document.getElementById('deptFilter').value;
  if (dept === 'all') { renderDoctors(allDoctors); return; }
  renderDoctors(allDoctors.filter(d =>
    (d.department || d.specialization || '').toLowerCase() === dept.toLowerCase()
  ));
}

/* ── CREATE DOCTOR ── */
async function createDoctor() {
  const name    = document.getElementById('newDoctorName').value.trim();
  const dept    = document.getElementById('newDoctorDept').value;
  const region  = document.getElementById('newDoctorRegion').value;
  const qual    = document.getElementById('newDoctorQual').value.trim();
  const exp     = document.getElementById('newDoctorExp').value;
  const days    = document.getElementById('newDoctorDays').value.trim();
  const hours   = document.getElementById('newDoctorHours').value.trim() || '8:00 AM - 8:00 PM';
  const docId   = document.getElementById('newDoctorId').value.trim();
  const pass    = document.getElementById('newDoctorPass').value.trim();
  const msgEl   = document.getElementById('createDoctorMsg');

  msgEl.style.color = '#ef9a9a';
  if (!name || !dept || !region || !qual || !exp || !days || !docId || !pass) {
    msgEl.innerText = 'Please fill in all required fields (including Region).'; return;
  }

  const hoursPattern = /^\d{1,2}:\d{2} (AM|PM) - \d{1,2}:\d{2} (AM|PM)$/;
  if (!hoursPattern.test(hours)) {
    msgEl.innerText = 'Hours format must be: H:MM AM/PM - H:MM AM/PM  e.g. 6:00 PM - 8:00 PM';
    return;
  }

  try {
    const res = await fetch(`${API}/admin-api/add-doctor`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        name,
        department:       dept,
        region:           region,
        qualification:    qual,
        experience_years: parseInt(exp),
        available_days:   days,
        available_hours:  hours,
        doc_id:           docId,
        password:         pass,
      }),
    });
    const data = await res.json();
    if (data.success) {
      msgEl.style.color = '#69f0ae';
      msgEl.innerText = `✓ Doctor created in ${region}!  ID: ${docId}   Password: ${pass}`;
      ['newDoctorName','newDoctorQual','newDoctorExp',
       'newDoctorDays','newDoctorHours','newDoctorId','newDoctorPass'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
      });
      document.getElementById('newDoctorDept').value = '';
      document.getElementById('newDoctorRegion').value = '';
    } else {
      msgEl.innerText = data.message || 'Something went wrong.';
    }
  } catch(e) {
    msgEl.innerText = 'Could not connect to server.';
  }
}

/* ── APPOINTMENTS ── */
async function loadAppointments() {
  const table = document.getElementById('appointmentsTable');
  try {
    const res  = await fetch(`${API}/admin-api/appointments`);
    const data = await res.json();
    allAppointments = data;
    renderAppointments(allAppointments);
  } catch(e) {
    table.innerHTML = `<tr><td colspan="7" class="empty-row">Could not load</td></tr>`;
  }
}

function renderAppointments(list) {
  const table = document.getElementById('appointmentsTable');
  table.innerHTML = '';
  if (!list.length) {
    table.innerHTML = `<tr><td colspan="8" class="empty-row">No appointments found</td></tr>`;
    return;
  }
  list.forEach(a => {
    const status = a.status || '—';
    table.innerHTML += `
      <tr>
        <td>${a.id || '—'}</td>
        <td>${a.patient || a.patient_name || '—'}</td>
        <td>${a.doctor  || a.doctor_name  || '—'}</td>
        <td>${a.department || a.specialization || '—'}</td>
        <td>${a.region || '—'}</td>
        <td>${a.date || '—'}</td>
        <td>${a.time || '—'}</td>
        <td><span class="badge badge-${status.toLowerCase()}">${status}</span></td>
      </tr>`;
  });
}

/* ── APPOINTMENT FILTERS ── */
function filterAppointments() {
  const dept   = document.getElementById('apptDeptFilter').value;
  const date   = document.getElementById('apptDateFilter').value;
  const status = document.getElementById('apptStatusFilter').value;

  let filtered = allAppointments;
  if (dept !== 'all')
    filtered = filtered.filter(a => (a.department || a.specialization || '').toLowerCase() === dept.toLowerCase());
  if (date)
    filtered = filtered.filter(a => a.date === date);
  if (status !== 'all')
    filtered = filtered.filter(a => (a.status || '').toLowerCase() === status.toLowerCase());

  renderAppointments(filtered);
}

function clearApptFilters() {
  document.getElementById('apptDeptFilter').value   = 'all';
  document.getElementById('apptDateFilter').value   = '';
  document.getElementById('apptStatusFilter').value = 'all';
  renderAppointments(allAppointments);
}

/* ── RATINGS & REVIEWS ── */
let allRatings = [];

async function loadRatings() {
  const table = document.getElementById('ratingsTable');
  try {
    const res  = await fetch(`${API}/admin-api/ratings`);
    const data = await res.json();
    allRatings = data;
    renderRatings(allRatings);
  } catch(e) {
    table.innerHTML = `<tr><td colspan="6" class="empty-row">Could not load ratings</td></tr>`;
  }
}

function renderRatings(list) {
  const table = document.getElementById('ratingsTable');
  table.innerHTML = '';
  if (!list.length) {
    table.innerHTML = `<tr><td colspan="6" class="empty-row">No ratings found</td></tr>`;
    return;
  }
  list.forEach(r => {
    const isLow = r.rating <= 3;
    const stars = '★'.repeat(r.rating) + '☆'.repeat(5 - r.rating);
    table.innerHTML += `
      <tr style="${isLow ? 'background:rgba(239,83,80,0.07);' : ''}">
        <td>${esc(r.patient)}</td>
        <td>${esc(r.doctor)}</td>
        <td>${esc(r.department)}</td>
        <td style="color:${isLow ? '#ef9a9a' : '#f5a623'}; font-size:1.1rem;">${stars}</td>
        <td>${r.review
          ? `<span style="color:${isLow ? '#ef9a9a' : '#a0aec0'}; font-style:italic;">"${esc(r.review)}"</span>`
          : '<span style="color:#4a5568;">—</span>'
        }</td>
        <td>${esc(r.date)}</td>
      </tr>`;
  });
}

function filterRatings() {
  const filter = document.getElementById('ratingsFilter').value;
  if (filter === 'all')  return renderRatings(allRatings);
  if (filter === 'low')  return renderRatings(allRatings.filter(r => r.rating <= 3));
  if (filter === 'high') return renderRatings(allRatings.filter(r => r.rating >= 4));
}

/* ── ADD LEAVE ── */
async function addLeave() {
  const name  = document.getElementById('staffName').value.trim();
  const date  = document.getElementById('leaveDate').value;
  const msgEl = document.getElementById('leaveMsg');

  msgEl.style.color = '#ef9a9a';
  if (!name || !date) { msgEl.innerText = 'Please fill in both fields.'; return; }

  try {
    const res  = await fetch(`${API}/admin-api/leave`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, date }),
    });
    const data = await res.json();
    msgEl.style.color = '#69f0ae';
    msgEl.innerText = data.message || 'Leave added!';
    document.getElementById('staffName').value = '';
    document.getElementById('leaveDate').value = '';
  } catch(e) { msgEl.innerText = 'Could not connect.'; }
}

/* ── LOGOUT ── */
function logout() {
  localStorage.clear();
  window.location.href = '../pages/login.html';
}

/* ── INIT ── */
document.addEventListener('DOMContentLoaded', () => {
  loadOverview();
});