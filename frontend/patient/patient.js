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
    table.innerHTML = `<tr><td colspan="7" class="empty-row">Not logged in.</td></tr>`;
    return;
  }

  try {
    const res  = await fetch(`${BACKEND}/patient/appointments?patient_id=${patientId}`);
    const data = await res.json();
    const list = data.appointments || data;

    table.innerHTML = "";

    if (!list || !list.length) {
      table.innerHTML = `<tr><td colspan="7" class="empty-row">No appointments found.</td></tr>`;
      return;
    }

    list.forEach(a => {
      const status = a.status || "Pending";
      let statusClass = "status-pending";
      if (status.toLowerCase() === "confirmed" || status.toLowerCase() === "scheduled") statusClass = "status-confirmed";
      else if (status.toLowerCase() === "cancelled") statusClass = "status-cancelled";
      else if (status.toLowerCase() === "completed") statusClass = "status-completed";
      
      table.innerHTML += `
        <tr>
          <td>${a.appointment_id || a.id || "-"}</td>
          <td>${a.doctor || a.doctor_name || "-"}</td>
          <td>${a.doctor_phone || a.contact_phone || "-"}</td>
          <td>${a.doctor_email || a.email || "-"}</td>
          <td>${a.date || "-"}</td>
          <td>${a.time || "-"}</td>
          <td><span class="status-badge ${statusClass}">${status}</span></td>
        </tr>
      `;
    });

    document.getElementById("appointmentCount").innerText = list.length;

  } catch (err) {
    table.innerHTML = `<tr><td colspan="7" class="empty-row">Could not load appointments.</td></tr>`;
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

    if (!list || !list.length) {
      table.innerHTML = `<tr><td colspan="3" class="empty-row">No records found.</td></tr>`;
      return;
    }

    list.forEach(r => {
      table.innerHTML += `
        <tr>
          <td>${r.doctor || r.doctor_name || "—"}</td>
          <td>${r.diagnosis || "—"}</td>
          <td>${r.date || "—"}</td>
        </tr>
      `;
    });

    document.getElementById("reportCount").innerText = list.length;

  } catch (err) {
    table.innerHTML = `<tr><td colspan="3" class="empty-row">No records available.</td></tr>`;
    console.error("Failed to load records:", err);
  }
}

/* ── Load dashboard stats ── */
async function loadDashboardStats() {
  const patientId = localStorage.getItem("patient_id");
  
  if (!patientId) return;
  
  try {
    // Get unique doctors from appointments
    const appointmentsRes = await fetch(`${BACKEND}/patient/appointments?patient_id=${patientId}`);
    const appointmentsData = await appointmentsRes.json();
    const appointments = appointmentsData.appointments || appointmentsData;
    
    // Count unique doctors
    const uniqueDoctors = new Set();
    if (appointments && appointments.length) {
      appointments.forEach(a => {
        if (a.doctor || a.doctor_name) {
          uniqueDoctors.add(a.doctor || a.doctor_name);
        }
      });
    }
    document.getElementById("doctorCount").innerText = uniqueDoctors.size || "0";
    
  } catch (err) {
    console.error("Failed to load stats:", err);
  }
}

/* ── Logout ── */
function logout() {
  if (confirm("Are you sure you want to logout?")) {
    localStorage.clear();
    window.location.href = "../login.html";
  }
}

/* ── Rating Modal Functions ── */
let currentRatingApptId = null;
let currentRating = 0;

function openRating(apptId, doctorName) {
  currentRatingApptId = apptId;
  currentRating = 0;
  
  // Create modal if it doesn't exist
  let modal = document.getElementById('ratingModal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'ratingModal';
    modal.className = 'modal';
    modal.innerHTML = `
      <div class="modal-content">
        <h3>Rate Dr. <span id="ratingDoctorName"></span></h3>
        <div id="stars" class="rating-stars">
          <span onclick="setRating(1)">★</span>
          <span onclick="setRating(2)">★</span>
          <span onclick="setRating(3)">★</span>
          <span onclick="setRating(4)">★</span>
          <span onclick="setRating(5)">★</span>
        </div>
        <textarea id="reviewText" placeholder="Write your review (optional)..." rows="3"></textarea>
        <div class="modal-buttons">
          <button onclick="submitRating()" class="btn-submit">Submit</button>
          <button onclick="closeRating()" class="btn-cancel">Cancel</button>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
  }
  
  document.getElementById('ratingDoctorName').textContent = doctorName;
  document.getElementById('reviewText').value = '';
  highlightStars(0);
  modal.style.display = 'flex';
}

function closeRating() {
  const modal = document.getElementById('ratingModal');
  if (modal) modal.style.display = 'none';
}

function setRating(val) {
  currentRating = val;
  highlightStars(val);
}

function highlightStars(val) {
  const stars = document.querySelectorAll('#stars span');
  stars.forEach((s, i) => {
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
    const response = await fetch(`${BACKEND}/patient/rate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        appointment_id: currentRatingApptId,
        rating: currentRating,
        review: review
      })
    });
    
    if (response.ok) {
      alert('Thank you for your feedback!');
      closeRating();
    } else {
      alert('Failed to submit rating. Please try again.');
    }
  } catch(e) {
    console.error("Rating error:", e);
    alert('Could not submit rating. Please try again later.');
  }
  closeRating();
}

/* ── Add rating button to appointments (optional) ── */
// This function adds rate buttons for completed appointments
async function addRatingButtons() {
  const patientId = localStorage.getItem("patient_id");
  if (!patientId) return;
  
  try {
    const res = await fetch(`${BACKEND}/patient/appointments?patient_id=${patientId}`);
    const data = await res.json();
    const list = data.appointments || data;
    
    if (list && list.length) {
      list.forEach(async (a) => {
        if (a.status && a.status.toLowerCase() === 'completed') {
          // Check if already rated
          const ratingCheck = await fetch(`${BACKEND}/patient/check-rating?appointment_id=${a.appointment_id || a.id}`);
          const ratingData = await ratingCheck.json();
          
          if (!ratingData.rated) {
            // Add rate button logic here if needed
          }
        }
      });
    }
  } catch(e) {
    console.error("Error checking ratings:", e);
  }
}

/* ── Initialize everything on page load ── */
document.addEventListener("DOMContentLoaded", () => {
  loadAppointments();
  loadRecords();
  loadDashboardStats();
});

/* ── Make functions global for HTML onclick ── */
window.showSection = showSection;
window.logout = logout;
window.openRating = openRating;
window.closeRating = closeRating;
window.setRating = setRating;
window.submitRating = submitRating;