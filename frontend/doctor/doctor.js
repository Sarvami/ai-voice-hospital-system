// doctor.js
const API = "http://127.0.0.1:8000";
const params = new URLSearchParams(window.location.search);
const doctor_id = params.get("doctor_id");

async function fetchJSON(url, opts={}) {
  const r = await fetch(url, opts);
  return r.json();
}

async function loadProfile() {
  const d = await fetchJSON(`${API}/doctor/${doctor_id}`);
  document.getElementById("profile").innerHTML = JSON.stringify(d);
}

async function updateProfile(data) {
  await fetchJSON(`${API}/doctor/${doctor_id}`, {
    method: "PUT",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(data)
  });
  loadProfile();
}

async function loadAppointments() {
  const a = await fetchJSON(`${API}/doctor/${doctor_id}/appointments`);
  document.getElementById("appointments").innerHTML = JSON.stringify(a);
}

async function loadPatients() {
  const p = await fetchJSON(`${API}/doctor/${doctor_id}/patients`);
  document.getElementById("patients").innerHTML = JSON.stringify(p);
}

async function saveRecord(patient_id, record) {
  await fetchJSON(`${API}/doctor/${doctor_id}/records`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({patient_id, record})
  });
}

async function generatePrescription(patient_id, prescription) {
  await fetchJSON(`${API}/doctor/${doctor_id}/prescription`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({patient_id, prescription})
  });
}

loadProfile();
loadAppointments();
loadPatients();
