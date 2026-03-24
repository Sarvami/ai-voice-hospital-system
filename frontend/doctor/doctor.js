const API = "http://127.0.0.1:8000";

/* SWITCH */
function showSection(section) {
  document.querySelectorAll(".section").forEach(s => {
    s.classList.add("hidden");
  });
  document.getElementById(section).classList.remove("hidden");

  // Load ratings only when that tab is clicked
  if (section === 'ratings') loadRatings();

  // Update active sidebar item
  document.querySelectorAll(".sidebar ul li").forEach(l => l.classList.remove("active"));
  event.currentTarget.classList.add("active");
}

async function loadDoctor(){
    try {
        const doctorId = localStorage.getItem("doctor_id");
        const res = await fetch(`${API}/doctor/dashboard?doctor_id=${doctorId}`);
        const data = await res.json();

        const table = document.getElementById("doctorTable");
        table.innerHTML = `
            <tr>
                <td>${data.name}</td>
                <td>${data.specialization}</td>
                <td>${data.appointments_today}</td>
                <td>${data.total_patients}</td>
                <td>${renderStars(data.rating)}</td>
            </tr>
        `;
    } catch(e) {
        console.log("Error loading doctor:", e);
    }
}

async function loadAppointments(){
    try {
        const doctorId = localStorage.getItem("doctor_id");
        const res = await fetch(`${API}/doctor/appointments?doctor_id=${doctorId}`);
        const data = await res.json();

        const table = document.getElementById("appointmentTable");
        table.innerHTML = "";

        if (data.length === 0) {
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
                </tr>
            `;
        });
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

  // Build printable HTML
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
      </script>
    </body>
    </html>
  `);
  win.document.close();

  // Clear fields
  document.getElementById('pname').value    = '';
  document.getElementById('medicine').value = '';
  document.getElementById('dosage').value   = '';
}

/* LOGOUT */
function logout(){
localStorage.clear();
window.location.href="../login.html";
}

/* INIT */
loadDoctor();
loadAppointments();
async function loadRatings() {
  const doctorId = localStorage.getItem('doctor_id');
  const tbody    = document.getElementById('ratingsTable');

  try {
    const res  = await fetch(`${API}/doctor/ratings?doctor_id=${doctorId}`);
    const data = await res.json();
    const list = data.ratings || [];

    // Average score
    if (list.length) {
      const avg = list.reduce((s, r) => s + r.rating, 0) / list.length;
      document.getElementById('avgScore').textContent    = avg.toFixed(1) + ' / 5';
      document.getElementById('totalReviews').textContent = list.length + ' reviews';
      document.getElementById('avgStars').textContent    = '★'.repeat(Math.round(avg)) + '☆'.repeat(5 - Math.round(avg));
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
    tbody.innerHTML = `<tr><td colspan="4" class="empty-row">Could not load ratings</td></tr>`;
  }
}