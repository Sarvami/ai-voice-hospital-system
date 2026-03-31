const API = "http://127.0.0.1:8000";

/* SWITCH SECTIONS */
function showSection(section) {
  document.querySelectorAll(".section").forEach(s => {
    s.classList.add("hidden");
  });
  document.getElementById(section).classList.remove("hidden");

  document.querySelectorAll(".sidebar ul li").forEach(l => l.classList.remove("active"));
  event.currentTarget.classList.add("active");
}

/* LOAD OVERVIEW */
async function loadOverview() {
  try {
    const res = await fetch(`${API}/admin/overview`);
    const data = await res.json();
    document.getElementById("totalPatients").innerText = data.patients || 0;
    document.getElementById("totalDoctors").innerText = data.doctors || 0;
    document.getElementById("totalAppointments").innerText = data.appointments || 0;
  } catch (e) {
    console.error("Failed to load overview:", e);
  }
}

/* LOAD PATIENTS */
async function loadPatients() {
  try {
    const res = await fetch(`${API}/admin/patients`);
    const data = await res.json();
    const table = document.getElementById("patientsTable");
    table.innerHTML = "";
    if (!data.length) {
      table.innerHTML = `<tr><td colspan="3">No patients found.</td></tr>`;
      return;
    }
    data.forEach(p => {
      table.innerHTML += `
        <tr>
          <td>${p.name || "—"}</td>
          <td>${p.age || "—"}</td>
          <td>${p.phone || "—"}</td>
        </tr>`;
    });
  } catch (e) {
    console.error("Failed to load patients:", e);
  }
}

/* LOAD DOCTORS */
async function loadDoctors() {
  try {
    const res = await fetch(`${API}/admin/doctors`);
    const data = await res.json();
    const table = document.getElementById("doctorsTable");
    table.innerHTML = "";
    if (!data.length) {
      table.innerHTML = `<tr><td colspan="3">No doctors found.</td></tr>`;
      return;
    }
    data.forEach(d => {
      table.innerHTML += `
        <tr>
          <td>${d.name || "—"}</td>
          <td>${d.department || "—"}</td>
          <td>${d.experience_years || "—"}</td>
        </tr>`;
    });
  } catch (e) {
    console.error("Failed to load doctors:", e);
  }
}

/* LOAD APPOINTMENTS */
async function loadAppointments() {
  try {
    const res = await fetch(`${API}/admin/appointments`);
    const data = await res.json();
    const table = document.getElementById("appointmentsTable");
    table.innerHTML = "";
    if (!data.length) {
      table.innerHTML = `<tr><td colspan="5">No appointments found.</td></tr>`;
      return;
    }
    data.forEach(a => {
      table.innerHTML += `
        <tr>
          <td>${a.appointment_id || "—"}</td>
          <td>${a.patient || "—"}</td>
          <td>${a.doctor || "—"}</td>
          <td>${a.date || "—"}</td>
          <td>${a.time || "—"}</td>
        </tr>`;
    });
  } catch (e) {
    console.error("Failed to load appointments:", e);
  }
}

/* ASSIGN NURSE */
function assignNurse() {
  const doctor = document.getElementById("doctorName").value;
  const nurse = document.getElementById("nurseName").value;
  fetch(`${API}/admin/assign-nurse`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doctor, nurse })
  });
  alert("Nurse Assigned");
}

/* ADD LEAVE */
function addLeave() {
  const name = document.getElementById("staffName").value;
  const date = document.getElementById("leaveDate").value;
  fetch(`${API}/admin/leave`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, date })
  });
  alert("Leave Added");
}

/* LOGOUT */
function logout() {
  localStorage.clear();
  window.location.href = "../login.html";
}

/* INIT */
loadOverview();
loadPatients();
loadDoctors();
loadAppointments();