const API = "http://127.0.0.1:8000";

const params = new URLSearchParams(window.location.search);
const doctor_id = params.get("doctor_id");


async function fetchJSON(url, opts={}){
const r = await fetch(url,opts);
return r.json();
}


async function loadAppointments(){

const data = await fetchJSON(`${API}/doctor/${doctor_id}/appointments`);

const table = document.getElementById("appointments");
table.innerHTML="";

data.forEach(a=>{

table.innerHTML += `
<tr>
<td>${a.patient_name}</td>
<td>${a.time}</td>
<td>${a.reason}</td>
</tr>
`;

});

document.getElementById("todayAppointments").innerText=data.length;

}


async function loadPatients(){

const data = await fetchJSON(`${API}/doctor/${doctor_id}/patients`);

const table = document.getElementById("patients");
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

document.getElementById("totalPatients").innerText=data.length;

}


function logout(){

localStorage.clear();
window.location.href="../login.html";

}


loadAppointments();
loadPatients();