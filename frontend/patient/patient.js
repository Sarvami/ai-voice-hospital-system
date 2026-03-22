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
        <tr>
          <td>${a.appointment_id || a.id || "—"}</td>
          <td>${a.doctor || a.doctor_name || "—"}</td>
          <td>${a.date || "—"}</td>
          <td>${a.time || "—"}</td>
          <td>${a.status || "—"}</td>
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

    list.forEach(r => {
      table.innerHTML += `
        <tr>
          <td>${r.doctor || r.doctor_name || "—"}</td>
          <td>${r.diagnosis || "—"}</td>
          <td>${r.date || "—"}</td>
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