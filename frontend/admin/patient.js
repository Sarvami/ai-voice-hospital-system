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