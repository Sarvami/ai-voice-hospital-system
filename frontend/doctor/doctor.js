const API = "http://127.0.0.1:8000";

/* SWITCH */
function showSection(section, element) {
  document.querySelectorAll(".section").forEach(s => {
    s.classList.add("hidden");
  });
  const targetSection = document.getElementById(section);
  if (targetSection) targetSection.classList.remove("hidden");

  if (section === 'ratings') loadRatings();
  if (section === 'patients') loadPatients();
  if (section === 'appointments') loadAppointments();

  // If element is not provided (e.g. clicked from a card), find the sidebar item manually
  if (!element) {
    const sidebarItems = document.querySelectorAll(".sidebar ul li");
    if (section === 'dashboard') element = sidebarItems[0];
    else if (section === 'appointments') element = sidebarItems[1];
    else if (section === 'prescription') element = sidebarItems[2];
    else if (section === 'ratings') element = sidebarItems[3];
    else if (section === 'patients') element = sidebarItems[4];
  }

  if (element) {
    document.querySelectorAll(".sidebar ul li").forEach(l => l.classList.remove("active"));
    element.classList.add("active");
  }
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

async function loadAppointments(){  // ✅ fixed: was "aasync"
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
        <h1>🎙️ AI Voice Hospital</h1>
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
          AI Voice Hospital
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
    table.innerHTML = "<tr><td colspan='4'>No appointments on this date.</td></tr>";
    return;
  }
  filtered.forEach(a => {
    table.innerHTML += `
      <tr>
        <td>${a.id}</td>
        <td>${a.patient_name}</td>
        <td>${a.date}</td>
        <td>${a.time}</td>
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
    table.innerHTML = "<tr><td colspan='4'>No appointments yet.</td></tr>";
    return;
  }
  data.forEach(a => {
    table.innerHTML += `
      <tr>
        <td>${a.id}</td>
        <td>${a.patient_name}</td>
        <td>${a.date}</td>
        <td>${a.time}</td>
      </tr>`;
  });
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
      tbody.innerHTML += `
        <tr>
          <td>${r.patient_name || '—'}</td>
          <td>${'★'.repeat(r.rating)}${'☆'.repeat(5 - r.rating)}</td>
          <td>${r.review || '—'}</td>
          <td>${r.date || '—'}</td>
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
    if (!data.length) {
      tbody.innerHTML = `<tr><td colspan="5" class="empty-row">No patients found</td></tr>`;
      return;
    }

    data.forEach(p => {
      tbody.innerHTML += `
        <tr>
          <td>${p.patient_id}</td>
          <td>${p.name}</td>
          <td>${p.age}</td>
          <td>${p.gender}</td>
          <td>${p.phone}</td>
        </tr>`;
    });

  } catch(e) {
    if (tbody) tbody.innerHTML = `<tr><td colspan="5" class="empty-row">Could not load patients</td></tr>`;
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
