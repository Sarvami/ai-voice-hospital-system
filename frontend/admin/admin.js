const API = window.location.origin;

let allDoctors      = [];
let allAppointments = [];

/* ── XSS helper ── */
function esc(str) {
  if (str === null || str === undefined) return '—';
  return String(str).replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
}

const sectionTitles = {
  overview:      'Overview',
  analytics:     'Analytics',
  patients:      'Patients',
  viewDoctors:   'Doctors — View',
  createDoctor:  'Doctors — Create',
  bulkImport:    'Bulk Import',
  appointments:  'Appointments',
  messages:      'Messages',
  leaves:        'Staff Leaves',
  ratings:       'Ratings & Reviews',
  announcements: 'Announcements',
  auditLog:      'Audit Log',
};

let chartAppts = null, chartDept = null, chartRegion = null;

function showSection(section, liEl) {
  document.querySelectorAll('.section').forEach(s => s.classList.add('hidden'));
  document.getElementById(section).classList.remove('hidden');
  document.querySelectorAll('.sidebar li').forEach(l => l.classList.remove('active'));
  if (liEl) liEl.classList.add('active');
  document.getElementById('currentPageTitle').textContent = sectionTitles[section] || '';
  if (section === 'patients')      loadPatients();
  if (section === 'viewDoctors')   loadDoctors();
  if (section === 'appointments')  loadAppointments();
  if (section === 'ratings')       loadRatings();
  if (section === 'analytics')     loadAnalytics();
  if (section === 'auditLog')      loadAuditLog();
  if (section === 'announcements') loadAnnouncements();
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
    const res  = await fetch(`${API}/api/admin/overview`);
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
  table.innerHTML = skeletonTableRows(8, 6);
  try {
    const res  = await fetch(`${API}/api/admin/patients`);
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
            <div class="patient-actions">
              <i class="fa-solid fa-pen-to-square" title="Edit" onclick="openEditModal(${p.patient_id})"></i>
              <i class="fa-solid fa-paper-plane" title="Message Patient" style="color:#69f0ae;" onclick="openMessageModal(${p.patient_id}, '${esc(p.name)}')"></i>
              <i class="fa-solid fa-folder-open" title="View Reports" style="color:#38bdf8;" onclick="openReportsModal(${p.patient_id}, '${esc(p.name)}')"></i>
              <i class="fa-solid fa-trash" title="Delete Patient" style="color:#ef5350;" onclick="deletePatient(${p.patient_id}, '${esc(p.name)}')"></i>
            </div>
          </td>
        </tr>`;
    });
  } catch(e) {
    table.innerHTML = `<tr><td colspan="8" class="empty-row">Could not load</td></tr>`;
  }
}

async function deletePatient(id, name) {
  if (!confirm(`Delete patient "${name}" and all their appointments?`)) return;
  try {
    const res = await fetch(`${API}/api/admin/patients/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.success) loadPatients();
    else alert(data.message || 'Delete failed');
  } catch (e) {
    alert('Could not delete patient.');
  }
}

function filterPatientsTable() {
  const query = document.getElementById('patientSearchFilter').value.toLowerCase();
  const lang = document.getElementById('patientLangFilter').value;
  const gender = document.getElementById('patientGenderFilter').value;
  const ageRange = document.getElementById('patientAgeFilter').value;
  const table = document.getElementById('patientsTable');
  
  const filtered = allPatients.filter(p => {
    const matchesQuery = p.name.toLowerCase().includes(query) || p.email.toLowerCase().includes(query);
    const matchesLang = (lang === 'all') || (p.preferred_language === lang);
    const matchesGender = (gender === 'all') || (p.gender === gender);
    
    let matchesAge = true;
    if (ageRange !== 'all') {
      const [min, max] = ageRange.split('-').map(Number);
      matchesAge = p.age >= min && p.age <= max;
    }

    return matchesQuery && matchesLang && matchesGender && matchesAge;
  });

  table.innerHTML = '';
  if (!filtered.length) {
    table.innerHTML = `<tr><td colspan="8" class="empty-row">No patients found</td></tr>`;
    return;
  }

  filtered.forEach(p => {
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
          <div class="patient-actions">
            <i class="fa-solid fa-pen-to-square" title="Edit" onclick="openEditModal(${p.patient_id})"></i>
            <i class="fa-solid fa-paper-plane" title="Message Patient" style="color:#69f0ae;" onclick="openMessageModal(${p.patient_id}, '${esc(p.name)}')"></i>
            <i class="fa-solid fa-folder-open" title="View Reports" style="color:#38bdf8;" onclick="openReportsModal(${p.patient_id}, '${esc(p.name)}')"></i>
            <i class="fa-solid fa-trash" title="Delete Patient" style="color:#ef5350;" onclick="deletePatient(${p.patient_id}, '${esc(p.name)}')"></i>
          </div>
        </td>
      </tr>`;
  });
}

function clearPatientFilters() {
  document.getElementById('patientSearchFilter').value = '';
  document.getElementById('patientLangFilter').value = 'all';
  document.getElementById('patientGenderFilter').value = 'all';
  document.getElementById('patientAgeFilter').value = 'all';
  filterPatientsTable();
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
    const res = await fetch(`${API}/api/admin/update-patient`, {
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
    const res = await fetch(`${API}/api/admin/send-message`, {
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
  table.innerHTML = skeletonTableRows(11, 5);
  try {
    const res  = await fetch(`${API}/api/admin/doctors`);
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
        const res = await fetch(`${API}/api/admin/update-doctor`, {
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
    const res = await fetch(`${API}/api/admin/add-doctor`, {
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
  table.innerHTML = skeletonTableRows(8, 6);
  try {
    const res  = await fetch(`${API}/api/admin/appointments`);
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
  table.innerHTML = skeletonTableRows(6, 5);
  try {
    const res  = await fetch(`${API}/api/admin/ratings`);
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
    const res  = await fetch(`${API}/api/admin/leave`, {
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

/* ── ADMIN MESSAGING ── */
let activeAdminChatPatientId = null;
let adminMessagesPollTimer = null;

async function loadAdminConversations() {
    try {
        const res = await fetch(`${API}/api/admin/conversations`);
        const list = await res.json();
        const container = document.getElementById('adminConvList');
        
        if (!list.length) {
            container.innerHTML = '<div class="empty-conv">No conversations yet.</div>';
            return;
        }
        
        container.innerHTML = list.map(c => {
            const isActive = c.patient_id === activeAdminChatPatientId ? ' active' : '';
            return `
                <div class="admin-conversation-item${isActive}" onclick="openAdminChat(${c.patient_id}, '${esc(c.patient_name)}')">
                    <div class="conv-patient-name">👤 ${esc(c.patient_name)}</div>
                    <div class="conv-last-msg">${esc(c.last_message || '...')}</div>
                </div>`;
        }).join('');
    } catch(e) { console.error("loadAdminConversations error:", e); }
}

async function openAdminChat(patientId, patientName) {
    activeAdminChatPatientId = patientId;
    document.getElementById('adminChatHeader').textContent = `Chat with ${patientName}`;
    document.getElementById('adminChatInputArea').style.display = 'flex';
    document.getElementById('adminReplyInput').focus();
    
    // Highlight active
    document.querySelectorAll('.admin-conversation-item').forEach(el => el.classList.remove('active'));
    event && event.currentTarget && event.currentTarget.classList.add('active');
    
    await loadAdminMessages();
    loadAdminConversations(); // refresh list
}

async function loadAdminMessages() {
    if (activeAdminChatPatientId === null) return;
    try {
        const res = await fetch(`${API}/api/admin/messages/${activeAdminChatPatientId}`);
        const msgs = await res.json();
        const container = document.getElementById('adminChatMessages');
        
        container.innerHTML = msgs.map(m => {
            const isAdmin = m.sender_role === 'admin';
            const time = m.created_at ? new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';
            return `
                <div class="msg-bubble ${isAdmin ? 'msg-admin' : 'msg-patient'}">
                    ${esc(m.message_text)}
                    <span class="msg-time">${time}</span>
                </div>`;
        }).join('');
        container.scrollTop = container.scrollHeight;
    } catch(e) { console.error("loadAdminMessages error:", e); }
}

async function sendAdminReply() {
    const input = document.getElementById('adminReplyInput');
    const text = input.value.trim();
    if (!text || activeAdminChatPatientId === null) return;
    
    input.value = '';
    try {
        const res = await fetch(`${API}/api/admin/send-message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                receiver_id: activeAdminChatPatientId,
                message_text: text,
                sender_id: 0,
                sender_role: 'admin',
                receiver_role: 'patient'
            })
        });
        await loadAdminMessages();
        loadAdminConversations();
    } catch(e) { console.error("sendAdminReply error:", e); }
}

let adminWs = null;
let adminReconnectAttempts = 0;
const ADMIN_MAX_RECONNECT = 5;

async function setupAdminWebSocket() {
    try {
        const res = await fetch(`${API}/generate-ws-token?user_type=admin&user_id=0`);
        const data = await res.json();
        if (!data.token) throw new Error("No token received");

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/admin/0?token=${data.token}`;
        
        adminWs = new WebSocket(wsUrl);

        adminWs.onopen = () => {
            console.log("Admin WebSocket connected.");
            adminReconnectAttempts = 0;
            removeAdminOfflineBanner();
        };

        adminWs.onmessage = (event) => {
            try {
                const payload = JSON.parse(event.data);
                if (payload.type === "new_message") {
                    loadAdminConversations();
                    if (activeAdminChatPatientId !== null) loadAdminMessages();
                } else if (payload.type === "ping") {
                    adminWs.send("pong");
                }
            } catch(e) {}
        };

        adminWs.onclose = () => {
            console.log("Admin WebSocket disconnected.");
            attemptAdminReconnect();
        };
    } catch (err) {
        console.error("Failed to setup Admin WebSocket:", err);
        attemptAdminReconnect();
    }
}

function attemptAdminReconnect() {
    if (adminReconnectAttempts >= ADMIN_MAX_RECONNECT) {
        showAdminOfflineBanner();
        setInterval(() => {
            if (document.getElementById('messages').classList.contains('hidden')) return;
            loadAdminConversations();
            if (activeAdminChatPatientId !== null) loadAdminMessages();
        }, 5000);
        return;
    }
    
    const delay = Math.min(1000 * Math.pow(2, adminReconnectAttempts), 10000);
    adminReconnectAttempts++;
    setTimeout(setupAdminWebSocket, delay);
}

function showAdminOfflineBanner() {
    let banner = document.getElementById("adminOfflineBanner");
    if (!banner) {
        banner = document.createElement("div");
        banner.id = "adminOfflineBanner";
        banner.style.cssText = "position:fixed;top:0;left:0;width:100%;background:#ef5350;color:white;text-align:center;padding:10px;z-index:9999;font-weight:bold;";
        banner.textContent = "Connection Lost - Offline. Falling back to basic mode.";
        document.body.appendChild(banner);
    }
}

function removeAdminOfflineBanner() {
    const banner = document.getElementById("adminOfflineBanner");
    if (banner) banner.remove();
}

function startAdminMsgPolling() {
    // Replaced by WebSockets
}

/* ── OVERRIDE SHOWSECTION TO LOAD CONVERSATIONS ── */
const _origShowSection = window.showSection;
window.showSection = function(section, liEl) {
    _origShowSection(section, liEl);
    if (section === 'messages') {
        loadAdminConversations();
    }
};

window.openAdminChat = openAdminChat;
window.sendAdminReply = sendAdminReply;
window.showSection = showSection;

/* ── ANALYTICS ── */
async function loadAnalytics() {
  try {
    const res = await fetch(`${API}/api/admin/analytics`);
    const data = await res.json();
    const days = data.appointments_per_day || [];
    const depts = data.by_department || [];
    const regions = data.patients_by_region || [];

    const chartOpts = { responsive: true, maintainAspectRatio: true, plugins: { legend: { labels: { color: '#b0bec5' } } } };
    const gridColor = 'rgba(255,255,255,0.08)';

    if (chartAppts) chartAppts.destroy();
    chartAppts = new Chart(document.getElementById('chartApptsPerDay'), {
      type: 'line',
      data: {
        labels: days.map(d => d.day),
        datasets: [{ label: 'Appointments', data: days.map(d => d.count), borderColor: '#4fc3f7', backgroundColor: 'rgba(79,195,247,0.2)', fill: true, tension: 0.3 }],
      },
      options: { ...chartOpts, scales: { x: { ticks: { color: '#90a4ae' }, grid: { color: gridColor } }, y: { ticks: { color: '#90a4ae' }, grid: { color: gridColor } } } },
    });

    if (chartDept) chartDept.destroy();
    chartDept = new Chart(document.getElementById('chartDepartments'), {
      type: 'doughnut',
      data: {
        labels: depts.map(d => d.department),
        datasets: [{ data: depts.map(d => d.count), backgroundColor: ['#4fc3f7', '#69f0ae', '#ffa726', '#ef5350', '#ab47bc', '#26c6da', '#8d6e63', '#78909c'] }],
      },
      options: chartOpts,
    });

    if (chartRegion) chartRegion.destroy();
    chartRegion = new Chart(document.getElementById('chartRegions'), {
      type: 'bar',
      data: {
        labels: regions.map(r => r.region),
        datasets: [{ label: 'Patients', data: regions.map(r => r.count), backgroundColor: '#69f0ae' }],
      },
      options: { ...chartOpts, scales: { x: { ticks: { color: '#90a4ae' }, grid: { color: gridColor } }, y: { ticks: { color: '#90a4ae' }, grid: { color: gridColor } } } },
    });
  } catch (e) {
    console.error('Analytics load failed', e);
  }
}

/* ── AUDIT LOG ── */
async function loadAuditLog() {
  const table = document.getElementById('auditLogTable');
  table.innerHTML = skeletonTableRows(5, 8);
  try {
    const res = await fetch(`${API}/api/admin/audit-log`);
    const rows = await res.json();
    table.innerHTML = '';
    if (!rows.length) {
      table.innerHTML = '<tr><td colspan="5" class="empty-row">No audit entries yet.</td></tr>';
      return;
    }
    rows.forEach(r => {
      const det = typeof r.details === 'object' ? JSON.stringify(r.details) : (r.details || '');
      const time = r.created_at ? String(r.created_at).replace('T', ' ').slice(0, 19) : '—';
      table.innerHTML += `<tr>
        <td>${esc(time)}</td>
        <td>${esc(r.actor)}</td>
        <td>${esc(r.action)}</td>
        <td>${esc(r.entity_type)} #${esc(r.entity_id)}</td>
        <td style="max-width:280px; font-size:12px;">${esc(det)}</td>
      </tr>`;
    });
  } catch (e) {
    table.innerHTML = '<tr><td colspan="5" class="empty-row">Could not load audit log.</td></tr>';
  }
}

/* ── BULK IMPORT ── */
async function bulkImportDoctors() {
  const fileInput = document.getElementById('bulkCsvFile');
  const out = document.getElementById('bulkImportResult');
  if (!fileInput.files.length) {
    out.textContent = 'Please select a CSV file.';
    return;
  }
  const form = new FormData();
  form.append('file', fileInput.files[0]);
  out.textContent = 'Importing…';
  try {
    const res = await fetch(`${API}/api/admin/doctors/bulk-import`, { method: 'POST', body: form });
    const data = await res.json();
    if (data.success) {
      out.textContent = `Created: ${data.created}, Skipped: ${data.skipped}\n${(data.errors || []).join('\n')}`;
      fileInput.value = '';
      if (data.created) loadDoctors();
    } else {
      out.textContent = data.message || 'Import failed';
    }
  } catch (e) {
    out.textContent = 'Server error during import.';
  }
}

/* ── ANNOUNCEMENTS ── */
async function loadAnnouncements() {
  const list = document.getElementById('announceHistory');
  if (!list) return;
  list.innerHTML = '<li>Loading…</li>';
  try {
    const res = await fetch(`${API}/api/admin/announcements`);
    const rows = await res.json();
    list.innerHTML = rows.length
      ? rows.map(a => `<li><strong>${esc(a.title)}</strong> — ${esc(a.message)}<br><small>${esc(a.created_at)}</small></li>`).join('')
      : '<li>No announcements yet.</li>';
  } catch (e) {
    list.innerHTML = '<li>Could not load history.</li>';
  }
}

async function broadcastAnnouncement() {
  const title = document.getElementById('announceTitle').value.trim();
  const message = document.getElementById('announceMessage').value.trim();
  const msgEl = document.getElementById('announceMsg');
  if (!title || !message) {
    msgEl.style.color = '#ef9a9a';
    msgEl.textContent = 'Title and message are required.';
    return;
  }
  try {
    const res = await fetch(`${API}/api/admin/announcements/broadcast`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, message }),
    });
    const data = await res.json();
    if (data.success) {
      msgEl.style.color = '#69f0ae';
      msgEl.textContent = `Sent! ${data.patients_notified} patients notified (${data.push_sent || 0} push).`;
      document.getElementById('announceTitle').value = '';
      document.getElementById('announceMessage').value = '';
      loadAnnouncements();
    } else {
      msgEl.textContent = data.message || 'Failed';
    }
  } catch (e) {
    msgEl.textContent = 'Could not connect.';
  }
}

window.deletePatient = deletePatient;
window.bulkImportDoctors = bulkImportDoctors;
window.broadcastAnnouncement = broadcastAnnouncement;

/* ── INIT ── */
document.addEventListener('DOMContentLoaded', () => {
  loadOverview();
  setupAdminWebSocket();
  // If we are in the messages tab on load (unlikely but possible)
  if (!document.getElementById('messages').classList.contains('hidden')) {
      loadAdminConversations();
  }
});