console.log("Assistant script loaded");

// Elements
const recordBtn = document.getElementById("recordBtn"); // Ensure your HTML mic button has this ID
const statusText = document.getElementById("status");
const audioPlayer = document.getElementById("audioPlayer");

let mediaRecorder;
let audioChunks = [];
let selectedLanguage = "hi"; // Default to Hindi


/* ---------- PROFILE SECTION (STEP 3) ---------- */

const nameEl = document.getElementById("name");
const phoneEl = document.getElementById("phone");
const langEl = document.getElementById("language");

if (nameEl && phoneEl && langEl) {
  const name = localStorage.getItem("name");
  const phone = localStorage.getItem("phone");
  const lang = localStorage.getItem("lang");

  nameEl.innerText = name || "Unknown";
  phoneEl.innerText = phone || "Not available";
  langEl.innerText = lang || "Not set";
}


/* ---------- LOGOUT (STEP 4) ---------- */

const logoutBtn = document.getElementById("logoutBtn");

if (logoutBtn) {
  logoutBtn.addEventListener("click", () => {
    localStorage.clear();
    window.location.href = "login.html";
  });
}


/* ---------- 1. LANGUAGE SELECTION ---------- */
// This assumes your language buttons have the class "bubble" or "lang-btn"
document.querySelectorAll(".lang-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    // Remove active style from others, add to clicked
    document.querySelectorAll(".lang-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    
    // Get language code from data-lang attribute (e.g., data-lang="mr")
    selectedLanguage = btn.dataset.lang;
    console.log("Language switched to:", selectedLanguage);
    statusText.innerText = Ready for ${btn.innerText};
  });
});


/* ---------- 2. RECORD & PROCESS AUDIO ---------- */

recordBtn.addEventListener("click", async () => {
  if (!navigator.mediaDevices || !window.MediaRecorder) {
    alert("Recording not supported in this browser.");
    return;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    console.log("Microphone connected");

    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];

    mediaRecorder.start();
    statusText.innerText = "Listening...";
    recordBtn.classList.add("recording-pulse");

    mediaRecorder.ondataavailable = event => {
      audioChunks.push(event.data);
    };

    // Auto-stop after 5 seconds
    setTimeout(() => {
      if (mediaRecorder.state === "recording") {
        mediaRecorder.stop();
        statusText.innerText = "Processing...";
        recordBtn.classList.remove("recording-pulse");
      }
    }, 5000);

    mediaRecorder.onstop = async () => {

      const audioBlob = new Blob(audioChunks, { type: "audio/webm" });

      const formData = new FormData();
      formData.append("audio", audioBlob, "recording.webm");
      formData.append("language", selectedLanguage);

      try {
        const response = await fetch("http://127.0.0.1:8000/process-audio", {
          method: "POST",
          body: formData
        });

        if (!response.ok) throw new Error("Backend Error");

        const responseAudio = await response.blob();
        const audioUrl = URL.createObjectURL(responseAudio);

        audioPlayer.src = audioUrl;
        audioPlayer.play(); 

        statusText.innerText = "Response received ✨";

      } catch (err) {
        console.error("Fetch error:", err);
        statusText.innerText = "Error: Could not reach server";
      }
    };

  } catch (err) {
    console.error("Mic access error:", err);
    statusText.innerText = "Mic access denied";
  }
});