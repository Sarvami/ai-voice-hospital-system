const API = "http://127.0.0.1:8000";

/* ================= LOAD DOCTORS ================= */

async function loadDoctors(){

try{

const res = await fetch(`${API}/doctors`);
const data = await res.json();

const table = document.getElementById("doctorTable");

table.innerHTML = ""; // clear table

data.forEach(doc => {

table.innerHTML += `
<tr>
<td>${doc.name}</td>
<td>${doc.appointments}</td>
<td>${doc.patients}</td>
<td>
<div class="stars" onclick="rateDoctor(this)">
<i class="fa fa-star"></i>
<i class="fa fa-star"></i>
<i class="fa fa-star"></i>
<i class="fa fa-star"></i>
<i class="fa fa-star"></i>
</div>
</td>
</tr>
`;

});

}catch(err){
console.error("Error loading doctors:", err);
}

}

/* ================= RATING ================= */

function rateDoctor(container){

const stars = container.querySelectorAll("i");

stars.forEach((star,index)=>{

star.onclick = () => {

stars.forEach(s => s.style.color = "gray");

for(let i=0;i<=index;i++){
stars[i].style.color = "gold";
}

};

});

}

/* ================= SECTION SWITCH ================= */

function showSection(section){

document.querySelectorAll(".section").forEach(sec=>{
sec.classList.add("hidden");
});

document.getElementById(section).classList.remove("hidden");

}

/* ================= LOGOUT ================= */

function logout(){
localStorage.clear();
window.location.href="../login.html";
}

/* ================= INIT ================= */

loadDoctors();