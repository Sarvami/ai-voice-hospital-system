const API = "http://127.0.0.1:8000";

/* SWITCH */
function showSection(section){
document.querySelectorAll(".section").forEach(s=>{
s.classList.add("hidden");
});
document.getElementById(section).classList.remove("hidden");
}

/* LOAD OVERVIEW */
async function loadOverview(){
try{
const res = await fetch(`${API}/admin/overview`);
const data = await res.json();

document.getElementById("totalPatients").innerText = data.patients;
document.getElementById("totalDoctors").innerText = data.doctors;
document.getElementById("totalAppointments").innerText = data.appointments;

}catch(e){
console.log("No backend");
}
}

/* LOAD PATIENTS */
async function loadPatients(){
try{
const res = await fetch(`${API}/admin/patients`);
const data = await res.json();

const table = document.getElementById("patientsTable");
table.innerHTML="";

data.forEach(p=>{
table.innerHTML += `
<tr>
<td>${p.name}</td>
<td>${p.age}</td>
<td>${p.condition}</td>
</tr>
`;
});

}catch(e){}
}

/* LOAD DOCTORS */
async function loadDoctors(){
try{
const res = await fetch(`${API}/admin/doctors`);
const data = await res.json();

const table = document.getElementById("doctorsTable");
table.innerHTML="";

data.forEach(d=>{
table.innerHTML += `
<tr>
<td>${d.name}</td>
<td>${d.specialization}</td>
<td>${d.patients}</td>
</tr>
`;
});

}catch(e){}
}

/* LOAD APPOINTMENTS */
async function loadAppointments(){
try{
const res = await fetch(`${API}/admin/appointments`);
const data = await res.json();

const table = document.getElementById("appointmentsTable");
table.innerHTML="";

data.forEach(a=>{
table.innerHTML += `
<tr>
<td>${a.id}</td>
<td>${a.patient}</td>
<td>${a.doctor}</td>
<td>${a.date}</td>
<td>${a.time}</td>
</tr>
`;
});

}catch(e){}
}

/* ASSIGN NURSE */
function assignNurse(){
const doctor = document.getElementById("doctorName").value;
const nurse = document.getElementById("nurseName").value;

fetch(`${API}/admin/assign-nurse`,{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({doctor,nurse})
});

alert("Nurse Assigned");
}

/* LEAVE */
function addLeave(){
const name = document.getElementById("staffName").value;
const date = document.getElementById("leaveDate").value;

fetch(`${API}/admin/leave`,{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({name,date})
});

alert("Leave Added");
}

/* LOGOUT */
function logout(){
localStorage.clear();
window.location.href="../login.html";
}

/* INIT */
loadOverview();
loadPatients();
loadDoctors();
loadAppointments();