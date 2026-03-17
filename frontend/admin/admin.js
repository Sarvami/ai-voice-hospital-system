const API="http://127.0.0.1:8000";

async function fetchJSON(url,opts={}){

const r = await fetch(url,opts);
return r.json();

}


async function loadAppointments(){
    const patientId = localStorage.getItem("patient_id");
    const data = await fetchJSON(`${API}/admin/appointments?patient_id=${patientId}`);

table.innerHTML="";

data.forEach(a=>{

table.innerHTML+=`

<tr>
<td>${a.doctor}</td>
<td>${a.date}</td>
<td>${a.time}</td>
</tr>

`;

});

document.getElementById("appointmentCount").innerText=data.length;

}


function logout(){

localStorage.clear();
window.location.href="../login.html";

}

loadAppointments();