
function showSection(section){

const sections=document.querySelectorAll(".section")

sections.forEach(sec=>{
sec.classList.add("hidden")
})

document.getElementById(section).classList.remove("hidden")

}

/* logout */

function logout(){

localStorage.clear()

window.location.href="../login.html"

}

/* star rating */

const stars=document.querySelectorAll(".stars i")

stars.forEach((star,index)=>{

star.addEventListener("click",()=>{

stars.forEach(s=>s.style.color="gray")

for(let i=0;i<=index;i++){
stars[i].style.color="gold"
}

})

})