const API = "http://127.0.0.1:8000";

let allDoctors      = [];
let allAppointments = [];

const sectionTitles = {
  overview:     'Overview',
  patients:     'Patients',
  viewDoctors:  'Doctors — View',
  createDoctor: 'Doctors — Create',
  appointments: 'Appointments',
  nurses:       'Assign Nurses',
  leaves:       'Staff Leaves',
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
    const res  = await fetch(`${API}/admin/overview`);
    const data = await res.json();
    document.getElementById('totalPatients').innerText     = data.patients     ?? 0;
    document.getElementById('totalDoctors').innerText      = data.doctors      ?? 0;
    document.getElementById('totalAppointments').innerText = data.appointments ?? 0;
  } catch(e) {
    console.log('Backend not connected');
  }
}

/* ── PATIENTS ── */
async function loadPatients() {
  const table = document.getElementById('patientsTable');
  try {
    const res  = await fetch(`${API}/admin/patients`);
    const data = await res.json();
    table.innerHTML = '';
    if (!data.length) {
      table.innerHTML = `<tr><td colspan="3" class="empty-row">No patients found</td></tr>`;
      return;
    }
    data.forEach(p => {
      table.innerHTML += `
        <tr>
          <td>${p.name || '—'}</td>
          <td>${p.age  || '—'}</td>
          <td>${p.preferred_language || p.language || '—'}</td>
        </tr>`;
    });
  } catch(e) {
    table.innerHTML = `<tr><td colspan="3" class="empty-row">Could not load</td></tr>`;
  }
}

/* ── DOCTORS ── */
async function loadDoctors() {
  const table = document.getElementById('doctorsTable');
  try {
    const res  = await fetch(`${API}/admin/doctors`);
    const data = await res.json();
    allDoctors = data;
    renderDoctors(allDoctors);
  } catch(e) {
    table.innerHTML = `<tr><td colspan="9" class="empty-row">Could not load</td></tr>`;
  }
}

function renderDoctors(list) {
  const table = document.getElementById('doctorsTable');
  table.innerHTML = '';
  if (!list.length) {
    table.innerHTML = `<tr><td colspan="9" class="empty-row">No doctors found</td></tr>`;
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
      </tr>`;
  });
}

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
  const qual    = document.getElementById('newDoctorQual').value.trim();
  const exp     = document.getElementById('newDoctorExp').value;
  const days    = document.getElementById('newDoctorDays').value.trim();
  const hours   = document.getElementById('newDoctorHours').value.trim() || '8:00 AM - 8:00 PM';
  const docId   = document.getElementById('newDoctorId').value.trim();
  const pass    = document.getElementById('newDoctorPass').value.trim();
  const msgEl   = document.getElementById('createDoctorMsg');

  msgEl.style.color = '#ef9a9a';
  if (!name || !dept || !qual || !exp || !days || !docId || !pass) {
    msgEl.innerText = 'Please fill in all required fields.'; return;
  }

  const hoursPattern = /^\d{1,2}:\d{2} (AM|PM) - \d{1,2}:\d{2} (AM|PM)$/;
  if (!hoursPattern.test(hours)) {
    msgEl.innerText = 'Hours format must be: H:MM AM/PM - H:MM AM/PM  e.g. 6:00 PM - 8:00 PM';
    return;
  }

  try {
    const res = await fetch(`${API}/admin/add-doctor`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        name,
        department:       dept,
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
      msgEl.innerText = `✓ Doctor created!  ID: ${docId}   Password: ${pass}`;
      ['newDoctorName','newDoctorQual','newDoctorExp',
       'newDoctorDays','newDoctorHours','newDoctorId','newDoctorPass'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
      });
      document.getElementById('newDoctorDept').value = '';
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
    const res  = await fetch(`${API}/admin/appointments`);
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
    table.innerHTML = `<tr><td colspan="7" class="empty-row">No appointments found</td></tr>`;
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

/* ── ADD LEAVE ── */
async function addLeave() {
  const name  = document.getElementById('staffName').value.trim();
  const date  = document.getElementById('leaveDate').value;
  const msgEl = document.getElementById('leaveMsg');

  msgEl.style.color = '#ef9a9a';
  if (!name || !date) { msgEl.innerText = 'Please fill in both fields.'; return; }

  try {
    const res  = await fetch(`${API}/admin/leave`, {
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
  window.location.href = '../login.html';
}

/* ── INIT ── */
loadOverview();