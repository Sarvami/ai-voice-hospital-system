const BACKEND = "http://127.0.0.1:8000";

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
    table.innerHTML = `<tr><td colspan="5" class="empty-row">Not logged in.</td></tr>`;
    return;
  }

  try {
    const res  = await fetch(`${BACKEND}/patient/appointments?patient_id=${patientId}`);
    const data = await res.json();
    const list = data.appointments || data;

    table.innerHTML = "";

    if (!list.length) {
      table.innerHTML = `<tr><td colspan="5" class="empty-row">No appointments found.</td></tr>`;
      return;
    }

    list.forEach(a => {
      table.innerHTML += `
        table.innerHTML += `
  table.innerHTML += `
  <tr>
    <td>${a.appointment_id || a.id || "—"}</td>
    <td>${a.doctor || a.doctor_name || "—"}</td>
    <td>${a.date || "—"}</td>
    <td>${a.time || "—"}</td>
    <td>${a.status || "—"}</td>
    <td>${a.status === 'Completed' ?
      `<button onclick="openRating('${a.appointment_id || a.id}', '${a.doctor || a.doctor_name}')" class="btn-rate">⭐ Rate</button>`
      : '—'}</td>
  </tr>`;
    });

    document.getElementById("appointmentCount").innerText = list.length;

  } catch (err) {
    table.innerHTML = `<tr><td colspan="5" class="empty-row">Could not load appointments.</td></tr>`;
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

    if (!list.length) {
      table.innerHTML = `<tr><td colspan="3" class="empty-row">No records found.</td></tr>`;
      return;
    }

    list.forEach(a => {
  table.innerHTML += `
  <tr>
    <td>${a.appointment_id || a.id || "—"}</td>
    <td>${a.doctor || a.doctor_name || "—"}</td>
    <td>${a.date || "—"}</td>
    <td>${a.time || "—"}</td>
    <td>${a.status || "—"}</td>
    <td>${a.status === 'Completed' ?
      `<button onclick="openRating('${a.appointment_id || a.id}', '${a.doctor || a.doctor_name}')" class="btn-rate">⭐ Rate</button>`
      : '—'}</td>
  </tr>`;
});

    document.getElementById("reportCount").innerText = list.length;

  } catch (err) {
    table.innerHTML = `<tr><td colspan="3" class="empty-row">No records available.</td></tr>`;
  }
}

/* ── Logout ── */
function logout() {
  localStorage.clear();
  window.location.href = "../login.html";
}

/* ── Init ── */
loadAppointments();
loadRecords();
let currentRatingApptId = null;
let currentRating = 0;

function openRating(apptId, doctorName) {
  currentRatingApptId = apptId;
  currentRating = 0;
  document.getElementById('ratingDoctorName').textContent = doctorName;
  document.getElementById('reviewText').value = '';
  highlightStars(0);
  document.getElementById('ratingModal').style.display = 'flex';
}

function closeRating() {
  document.getElementById('ratingModal').style.display = 'none';
}

function setRating(val) {
  currentRating = val;
  highlightStars(val);
}

function highlightStars(val) {
  document.querySelectorAll('#stars span').forEach((s, i) => {
    s.style.color = i < val ? '#f5a623' : '#555';
  });
}

async function submitRating() {
  if (currentRating === 0) {
    alert('Please select a star rating.');
    return;
  }
  const review = document.getElementById('reviewText').value;
  try {
    await fetch(`${BACKEND}/patient/rate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        appointment_id: currentRatingApptId,
        rating: currentRating,
        review: review
      })
    });
  } catch(e) {}
  closeRating();
}