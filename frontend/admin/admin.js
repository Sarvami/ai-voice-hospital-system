// admin.js
const API = "http://127.0.0.1:8000";

async function fetchJSON(url, opts={}) {
  const r = await fetch(url, opts);
  return r.json();
}

async function loadStats() {
  const data = await fetchJSON(`${API}/admin/stats`);
  document.getElementById("stats").innerHTML = JSON.stringify(data);
}

async function loadDoctors() {
  const d = await fetchJSON(`${API}/admin/doctors`);
  document.getElementById("doctors").innerHTML = JSON.stringify(d);
}

async function loadPatients() {
  const p = await fetchJSON(`${API}/admin/patients`);
  document.getElementById("patients").innerHTML = JSON.stringify(p);
}

async function loadAppointments() {
  const a = await fetchJSON(`${API}/admin/appointments`);
  document.getElementById("appointments").innerHTML = JSON.stringify(a);
}

async function rescheduleAppointment(id, date, time) {
  await fetchJSON(`${API}/admin/appointments/${id}`, {
    method: "PUT",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({date, time})
  });
  loadAppointments();
}

async function assignNurse(doctor_id, nurse_name) {
  await fetchJSON(`${API}/admin/assign-nurse`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({doctor_id, nurse_name})
  });
}

async function loadVoiceNotes() {
  const v = await fetchJSON(`${API}/admin/voice-notes`);
  document.getElementById("voice").innerHTML = JSON.stringify(v);
}

loadStats();
loadDoctors();
loadPatients();
loadAppointments();
loadVoiceNotes();
