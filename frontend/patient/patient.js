function showSection(section){

document.querySelectorAll(".section").forEach(sec=>{
sec.classList.add("hidden");
});

document.getElementById(section).classList.remove("hidden");

}

/* ================= EMPTY TABLES (NO DUMMY) ================= */

function loadAppointments(){

const table = document.getElementById("appointmentsTable");
table.innerHTML = ""; // keep empty

}

function loadRecords(){

const table = document.getElementById("recordsTable");
table.innerHTML = ""; // keep empty

}

/* ================= LOGOUT ================= */

function logout(){
localStorage.clear();
window.location.href="../login.html";
}

/* ================= INIT ================= */

loadAppointments();
loadRecords();
const BACKEND = "http://127.0.0.1:8000";

function showSection(section) {
    document.querySelectorAll(".section").forEach(sec => {
        sec.classList.add("hidden");
    });
    document.getElementById(section).classList.remove("hidden");
}

async function loadAppointments() {
    const patientId = localStorage.getItem("patient_id");
    if (!patientId) return;

    try {
        const res = await fetch(`${BACKEND}/admin/appointments?patient_id=${patientId}`);
        const data = await res.json();

        const table = document.getElementById("appointmentsTable");
        table.innerHTML = "";

        if (data.length === 0) {
            table.innerHTML = "<tr><td colspan='5'>No appointments found.</td></tr>";
            return;
        }

        data.forEach(a => {
            table.innerHTML += `
                <tr>
                    <td>${a.appointment_id}</td>
                    <td>${a.doctor}</td>
                    <td>${a.date}</td>
                    <td>${a.time}</td>
                    <td>${a.status}</td>
                </tr>
            `;
        });

        document.getElementById("appointmentCount").innerText = data.length;

    } catch (err) {
        console.error("Failed to load appointments:", err);
    }
}

function loadRecords() {
    const table = document.getElementById("recordsTable");
    if (table) table.innerHTML = "<tr><td>No records available.</td></tr>";
}

function logout() {
    localStorage.clear();
    window.location.href = "../login.html";
}

loadAppointments();
loadRecords();