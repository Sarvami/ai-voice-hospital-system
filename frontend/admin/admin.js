/* =========================
   ADMIN LOGIN
========================= */

function login() {
  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;

  if (username === "admin" && password === "admin123") {
    localStorage.setItem("adminLoggedIn", "true");
    window.location.href = "admin_dashboard.html";
  } else {
    document.getElementById("error").innerText = "Invalid credentials";
  }
}

/* =========================
   AUTH CHECK
========================= */

function loadDashboard() {
  if (localStorage.getItem("adminLoggedIn") !== "true") {
    window.location.href = "admin_login.html";
    return;
  }

  fetchDoctors();
  fetchAppointments();
  fetchAnalytics();
}

/* =========================
   NAVIGATION
========================= */

function showSection(section) {
  document.querySelectorAll(".section").forEach(sec => {
    sec.classList.add("hidden");
  });
  document.getElementById(section).classList.remove("hidden");
}

function logout() {
  localStorage.removeItem("adminLoggedIn");
  window.location.href = "admin_login.html";
}

/* =========================
   FETCH DOCTORS
========================= */

async function fetchDoctors() {
  try {
    const res = await fetch("http://localhost:8000/admin/doctors");
    const doctors = await res.json();

    const table = document.getElementById("doctorTable");
    table.innerHTML = "";

    doctors.forEach(d => {
      table.innerHTML += `
        <tr>
          <td>${d.name}</td>
          <td>${d.department}</td>
          <td>${d.experience_years}</td>
          <td>${d.available_days}</td>
        </tr>`;
    });
  } catch {
    console.log("Backend not connected (doctors)");
  }
}

/* =========================
   FETCH APPOINTMENTS
========================= */

async function fetchAppointments() {
  try {
    const res = await fetch("http://localhost:8000/admin/appointments");
    const appointments = await res.json();

    const table = document.getElementById("appointmentTable");
    table.innerHTML = "";

    appointments.forEach(a => {
      table.innerHTML += `
        <tr>
          <td>${a.appointment_date}</td>
          <td>${a.appointment_time}</td>
          <td>${a.patient_name}</td>
          <td>${a.doctor_name}</td>
          <td>${a.language_used}</td>
          <td>${a.booking_source}</td>
        </tr>`;
    });
  } catch {
    console.log("Backend not connected (appointments)");
  }
}

/* =========================
   FETCH ANALYTICS
========================= */

async function fetchAnalytics() {
  try {
    const res = await fetch("http://localhost:8000/admin/stats/languages");
    const stats = await res.json();

    const list = document.getElementById("analyticsList");
    list.innerHTML = "";

    Object.keys(stats).forEach(lang => {
      list.innerHTML += `<li>${lang}: ${stats[lang]} bookings</li>`;
    });
  } catch {
    console.log("Backend not connected (analytics)");
  }
}
