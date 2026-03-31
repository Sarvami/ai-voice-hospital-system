const API = "http://127.0.0.1:8000";
let currentRescheduleId = null;
 
/* SWITCH SECTIONS */
function showSection(section, el) {
  document.querySelectorAll(".section").forEach(s => s.classList.add("hidden"));
  document.getElementById(section).classList.remove("hidden");
  document.querySelectorAll(".sidebar ul li").forEach(l => l.classList.remove("active"));
  if (el) el.classList.add("active");
 
  if (section === "patients") loadPatients();
  if (section === "doctors") loadDoctors();
  if (section === "appointments") loadAppointments();
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
      table.innerHTML = `<tr><td colspan="5">No patients found.</td></tr>`;
      return;
    }
    data.forEach(p => {
      table.innerHTML += `
        <tr>
          <td>${p.name || "—"}</td>
          <td>${p.age || "—"}</td>
          <td>${p.phone || "—"}</td>
          <td>${p.preferred_language || "—"}</td>
          <td>${p.created_at ? p.created_at.split(" ")[0] : "—"}</td>
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
      table.innerHTML = `<tr><td colspan="5">No doctors found.</td></tr>`;
      return;
    }
    data.forEach(d => {
      table.innerHTML += `
        <tr>
          <td>${d.name || "—"}</td>
          <td>${d.department || "—"}</td>
          <td>${d.qualification || "—"}</td>
          <td>${d.experience_years || "—"} yrs</td>
          <td>${d.available_days || "—"}</td>
        </tr>`;
    });
  } catch (e) {
    console.error("Failed to load doctors:", e);
  }
}
 
/* ADD DOCTOR */
async function addDoctor() {
  const name = document.getElementById("newDoctorName").value.trim();
  const dept = document.getElementById("newDoctorDept").value.trim();
  const qual = document.getElementById("newDoctorQual").value.trim();
  const exp = document.getElementById("newDoctorExp").value.trim();
  const phone = document.getElementById("newDoctorPhone").value.trim();
  const password = document.getElementById("newDoctorPassword").value.trim();
  const days = document.getElementById("newDoctorDays").value.trim();
  const msg = document.getElementById("doctorMsg");
 
  if (!name || !dept || !phone || !password) {
    msg.style.color = "#ef9a9a";
    msg.innerText = "Please fill in Name, Department, Phone and Password.";
    return;
  }
 
  try {
    const res = await fetch(`${API}/admin/add-doctor`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name, department: dept, qualification: qual,
        experience_years: parseInt(exp) || 0,
        phone, password, available_days: days
      })
    });
    const data = await res.json();
    if (data.success) {
      msg.style.color = "#69f0ae";
      msg.innerText = "✓ Doctor added successfully!";
      loadDoctors();
      loadOverview();
      document.getElementById("newDoctorName").value = "";
      document.getElementById("newDoctorDept").value = "";
      document.getElementById("newDoctorQual").value = "";
      document.getElementById("newDoctorExp").value = "";
      document.getElementById("newDoctorPhone").value = "";
      document.getElementById("newDoctorPassword").value = "";
      document.getElementById("newDoctorDays").value = "";
    } else {
      msg.style.color = "#ef9a9a";
      msg.innerText = data.message || "Failed to add doctor.";
    }
  } catch (e) {
    msg.style.color = "#ef9a9a";
    msg.innerText = "Could not connect to server.";
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
      table.innerHTML = `<tr><td colspan="7">No appointments found.</td></tr>`;
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
          <td>${a.status || "—"}</td>
          <td>
            <button onclick="openRescheduleModal(${a.appointment_id})"
              style="font-size:11px;padding:4px 10px;border-radius:6px;border:none;background:#4fc3f7;color:#0a0f1e;cursor:pointer;font-weight:600;">
              Reschedule
            </button>
          </td>
        </tr>`;
    });
  } catch (e) {
    console.error("Failed to load appointments:", e);
  }
}
 
/* SCHEDULE APPOINTMENT */
async function scheduleAppointment() {
  const phone = document.getElementById("apptPatientPhone").value.trim();
  const doctorId = document.getElementById("apptDoctorId").value.trim();
  const date = document.getElementById("apptDate").value;
  const time = document.getElementById("apptTime").value;
  const reason = document.getElementById("apptReason").value.trim();
  const msg = document.getElementById("apptMsg");
 
  if (!phone || !doctorId || !date || !time) {
    msg.style.color = "#ef9a9a";
    msg.innerText = "Please fill in all required fields.";
    return;
  }
 
  try {
    const res = await fetch(`${API}/admin/schedule-appointment`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ phone, doctor_id: parseInt(doctorId), date, time, reason })
    });
    const data = await res.json();
    if (data.success) {
      msg.style.color = "#69f0ae";
      msg.innerText = "✓ Appointment scheduled successfully!";
      loadAppointments();
      loadOverview();
      document.getElementById("apptPatientPhone").value = "";
      document.getElementById("apptDoctorId").value = "";
      document.getElementById("apptDate").value = "";
      document.getElementById("apptTime").value = "";
      document.getElementById("apptReason").value = "";
    } else {
      msg.style.color = "#ef9a9a";
      msg.innerText = data.message || "Failed to schedule.";
    }
  } catch (e) {
    msg.style.color = "#ef9a9a";
    msg.innerText = "Could not connect to server.";
  }
}
 
/* RESCHEDULE MODAL */
function openRescheduleModal(id) {
  currentRescheduleId = id;
  document.getElementById("newRescheduleDate").value = "";
  document.getElementById("newRescheduleTime").value = "";
  document.getElementById("rescheduleMsg").innerText = "";
  document.getElementById("rescheduleModal").classList.add("active");
}
 
function closeRescheduleModal() {
  document.getElementById("rescheduleModal").classList.remove("active");
  currentRescheduleId = null;
}
 
async function confirmReschedule() {
  const date = document.getElementById("newRescheduleDate").value;
  const time = document.getElementById("newRescheduleTime").value;
  const msg = document.getElementById("rescheduleMsg");
 
  if (!date || !time) {
    msg.style.color = "#ef9a9a";
    msg.innerText = "Please select both date and time.";
    return;
  }
 
  try {
    const res = await fetch(`${API}/admin/reschedule-appointment`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ appointment_id: currentRescheduleId, date, time })
    });
    const data = await res.json();
    if (data.success) {
      msg.style.color = "#69f0ae";
      msg.innerText = "✓ Rescheduled successfully!";
      setTimeout(() => {
        closeRescheduleModal();
        loadAppointments();
      }, 1000);
    } else {
      msg.style.color = "#ef9a9a";
      msg.innerText = data.message || "Failed to reschedule.";
    }
  } catch (e) {
    msg.style.color = "#ef9a9a";
    msg.innerText = "Could not connect to server.";
  }
}
 
/* LOGOUT */
function logout() {
  localStorage.clear();
  window.location.href = "../login.html";
}
 
/* INIT */
loadOverview();
 