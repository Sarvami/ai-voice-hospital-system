const API = "http://127.0.0.1:8000";

/* SWITCH */
function showSection(section){
document.querySelectorAll(".section").forEach(s=>{
s.classList.add("hidden");
});
document.getElementById(section).classList.remove("hidden");
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

/* PRESCRIPTION */
function savePrescription(){
alert("Prescription generated");
}

/* LOGOUT */
function logout(){
localStorage.clear();
window.location.href="../login.html";
}

/* INIT */
loadDoctor();
loadAppointments();