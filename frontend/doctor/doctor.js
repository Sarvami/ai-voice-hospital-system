const API = "http://127.0.0.1:8000";

/* SWITCH */
function showSection(section){
document.querySelectorAll(".section").forEach(s=>{
s.classList.add("hidden");
});
document.getElementById(section).classList.remove("hidden");
}

/* LOAD DOCTOR */
async function loadDoctor(){
try{
const res = await fetch(`${API}/doctor/dashboard`);
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

}catch(e){
console.log("No backend yet");
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

/* LOAD APPOINTMENTS */
async function loadAppointments(){
try{
const res = await fetch(`${API}/doctor/appointments`);
const data = await res.json();

const table = document.getElementById("appointmentTable");
table.innerHTML = "";

data.forEach(a=>{
table.innerHTML += `
<tr>
<td>${a.id}</td>
<td>${a.patient_name}</td>
<td>${a.date}</td>
<td>${a.time}</td>
</tr>
`;
});

}catch(e){
console.log("No backend yet");
}
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