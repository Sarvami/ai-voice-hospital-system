document.addEventListener("DOMContentLoaded", () => {

  const BACKEND = "http://127.0.0.1:8000";

  /* ================= PROFILE SECTION ================= */
  const nameEl  = document.getElementById("name");
  const phoneEl = document.getElementById("phone-display");
  const langEl  = document.getElementById("language");

  if (nameEl && phoneEl && langEl) {
    nameEl.innerText  = localStorage.getItem("name")  || "Unknown";
    phoneEl.innerText = localStorage.getItem("phone") || "Not available";
    langEl.innerText  = localStorage.getItem("lang")  || "Not set";
  }

  /* ================= REGISTER ================= */
  const registerBtn = document.getElementById("registerBtn");

  if (registerBtn) {
    registerBtn.addEventListener("click", async () => {
      const name     = document.getElementById("reg-name")?.value.trim();
      const age      = document.getElementById("reg-age")?.value.trim();
      const gender   = document.getElementById("reg-gender")?.value;
      const phone    = document.getElementById("reg-phone")?.value.trim();
      const password = document.getElementById("reg-password")?.value.trim();
      const language = document.getElementById("reg-language")?.value;
      const msg      = document.getElementById("reg-msg");

      if (!name || !age || !gender || !phone || !password) {
        msg.className = "msg error";
        msg.innerText = "Please fill in all fields";
        return;
      }

      if (phone.replace(/\D/g, "").length < 10) {
        msg.className = "msg error";
        msg.innerText = "Enter a valid 10-digit phone number";
        return;
      }

      try {
        const formData = new FormData();
        formData.append("name", name);
        formData.append("age", age);
        formData.append("gender", gender);
        formData.append("phone", phone.replace(/\D/g, "").slice(0, 10));
        formData.append("password", password);
        formData.append("language", language);

        const res  = await fetch(`${BACKEND}/register`, { method: "POST", body: formData });
        const data = await res.json();

        if (data.error) {
          msg.className = "msg error";
          msg.innerText = data.error;
          return;
        }

        msg.className = "msg success";
        msg.innerText = "Account created! Redirecting to login...";
        setTimeout(() => window.location.href = "login.html", 1500);

      } catch (err) {
        msg.className = "msg error";
        msg.innerText = "Cannot reach backend";
        console.error(err);
      }
    });
  }

  /* ================= LOGOUT ================= */
  const logoutBtn = document.getElementById("logoutBtn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
      localStorage.clear();
      window.location.href = "login.html";
    });
  }

  /* ================= DASHBOARD BUTTON ================= */
  const dashboardBtn = document.getElementById("dashboardBtn");
  if (dashboardBtn) {
    dashboardBtn.addEventListener("click", () => {
      window.location.href = "patient/patient_dashboard.html";
    });
  }

  /* ================= AUTH GUARD ================= */
  if (document.getElementById("recordBtn")) {
    const patientId = localStorage.getItem("patient_id");
    if (!patientId) {
      window.location.href = "login.html";
      return;
    }
  }

  /* ================= LANGUAGE SELECTION ================= */
  let selectedLang = localStorage.getItem("lang") || "hi";

  document.querySelectorAll(".bubble").forEach(btn => {
    if (btn.dataset.lang === selectedLang) btn.classList.add("active");

    btn.addEventListener("click", () => {
      document.querySelectorAll(".bubble").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      selectedLang = btn.dataset.lang;
      localStorage.setItem("lang", selectedLang);
      const statusText = document.getElementById("status");
      if (statusText) statusText.innerText = "Language selected ✔";
    });
  });

  /* ================= VOICE ASSISTANT ================= */
  const recordBtn   = document.getElementById("recordBtn");
  const statusText  = document.getElementById("status");
  const audioPlayer = document.getElementById("audioPlayer");
  const playBtn     = document.getElementById("playBtn");
  const progress    = document.getElementById("progress");
  const timeText    = document.getElementById("time");
  const subtitleBar = document.getElementById("subtitleBar");

  let mediaRecorder;
  let audioChunks = [];
  
  // Store conversation context
  let pendingIntent = null;
  let pendingDoctorId = null;

  if (recordBtn) {
    recordBtn.addEventListener("click", async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

        mediaRecorder  = new MediaRecorder(stream);
        audioChunks    = [];
        mediaRecorder.start();

        if (statusText) statusText.innerText = "Listening... 🎙️";
        recordBtn.style.background = "#ef5350";

        mediaRecorder.ondataavailable = e => audioChunks.push(e.data);

        setTimeout(() => {
          mediaRecorder.stop();
          stream.getTracks().forEach(t => t.stop());
          if (statusText) statusText.innerText = "Processing...";
          recordBtn.style.background = "";
        }, 5000);

        mediaRecorder.onstop = async () => {
          const audioBlob = new Blob(audioChunks, { type: "audio/wav" });

          const formData = new FormData();
          formData.append("audio", audioBlob, "recording.wav");
          formData.append("lang", selectedLang);
          formData.append("patient_id", localStorage.getItem("patient_id"));

          // Show loader
          if (typeof window.showLoader === 'function') {
            window.showLoader();
          } else if (typeof showLoader === 'function') {
            showLoader();
          }

          try {
            const res = await fetch(`${BACKEND}/process-audio`, { method: "POST", body: formData });

            // Hide loader
            if (typeof window.hideLoader === 'function') {
              window.hideLoader();
            } else if (typeof hideLoader === 'function') {
              hideLoader();
            }

            if (!res.ok) {
              if (statusText) statusText.innerText = "Backend error ❌";
              console.error("Backend error:", res.status);
              return;
            }

            const contentType = res.headers.get("content-type") || "";

            if (contentType.includes("application/json")) {
              const json = await res.json();
              
              console.log("JSON Response:", json); // Debug log

              // Show subtitle - FIXED
              if (subtitleBar) {
                if (json.text) {
                  subtitleBar.style.display = "block";
                  subtitleBar.textContent = json.text;
                  console.log("Subtitle displayed:", json.text);
                } else if (json.subtitle) {
                  subtitleBar.style.display = "block";
                  subtitleBar.textContent = json.subtitle;
                  console.log("Subtitle displayed:", json.subtitle);
                } else if (json.reply) {
                  subtitleBar.style.display = "block";
                  subtitleBar.textContent = json.reply;
                  console.log("Subtitle displayed:", json.reply);
                }
              }

              // Handle date request from bot
              if (json.text && (json.text.toLowerCase().includes("what date") || 
                  json.text.toLowerCase().includes("which date") ||
                  json.text.toLowerCase().includes("pick a date") ||
                  json.intent === "ask_date")) {
                
                pendingIntent = "date";
                if (json.doctor_id) pendingDoctorId = json.doctor_id;
                
                const selectedDate = await openCalendarPopup();
                if (selectedDate && pendingIntent === "date") {
                  showLoader();
                  try {
                    const dateResponse = await fetch(`${BACKEND}/set-appointment-date`, {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({ 
                        patient_id: localStorage.getItem("patient_id"),
                        date: selectedDate,
                        doctor_id: pendingDoctorId,
                        lang: selectedLang 
                      })
                    });
                    
                    const dateResult = await dateResponse.json();
                    if (dateResult.text && subtitleBar) {
                      subtitleBar.textContent = dateResult.text;
                    }
                    if (dateResult.audio_url && audioPlayer) {
                      audioPlayer.src = dateResult.audio_url;
                      audioPlayer.load();
                      audioPlayer.play();
                      if (playBtn) playBtn.textContent = "❚❚";
                    }
                  } catch (err) {
                    console.error("Date submission error:", err);
                  } finally {
                    hideLoader();
                  }
                }
                pendingIntent = null;
                return;
              }
              
              // Handle region request from bot
              if (json.text && (json.text.toLowerCase().includes("region") || 
                  json.text.toLowerCase().includes("hospital") ||
                  json.text.toLowerCase().includes("location") ||
                  json.intent === "ask_region")) {
                
                pendingIntent = "region";
                if (json.doctor_id) pendingDoctorId = json.doctor_id;
                
                const selectedRegion = await openRegionPopup();
                if (selectedRegion && pendingIntent === "region") {
                  showLoader();
                  try {
                    const regionResponse = await fetch(`${BACKEND}/set-region`, {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({ 
                        patient_id: localStorage.getItem("patient_id"),
                        region: selectedRegion,
                        doctor_id: pendingDoctorId,
                        lang: selectedLang 
                      })
                    });
                    
                    const regionResult = await regionResponse.json();
                    if (regionResult.text && subtitleBar) {
                      subtitleBar.textContent = regionResult.text;
                    }
                    if (regionResult.audio_url && audioPlayer) {
                      audioPlayer.src = regionResult.audio_url;
                      audioPlayer.load();
                      audioPlayer.play();
                      if (playBtn) playBtn.textContent = "❚❚";
                    }
                  } catch (err) {
                    console.error("Region submission error:", err);
                  } finally {
                    hideLoader();
                  }
                }
                pendingIntent = null;
                return;
              }

              // Show success popup if booking confirmed
              if (json.booked) {
                if (typeof window.showSuccessPopup === 'function') {
                  window.showSuccessPopup(json.success_message || "Your appointment has been successfully booked.");
                } else if (typeof showSuccessPopup === 'function') {
                  showSuccessPopup(json.success_message || "Your appointment has been successfully booked.");
                }
              }

              // Play audio if url provided
              if (json.audio_url && audioPlayer) {
                audioPlayer.src = json.audio_url;
                audioPlayer.load();
                audioPlayer.play();
                if (playBtn) playBtn.textContent = "❚❚";
              }

            } else {
              // Original flow: backend returns raw audio blob
              const audioData = await res.blob();
              const url       = URL.createObjectURL(audioData);

              if (audioPlayer) {
                audioPlayer.src = url;
                audioPlayer.load();
                audioPlayer.play();
                if (playBtn) playBtn.textContent = "❚❚";
              }
            }

            if (statusText) statusText.innerText = "Response received ✅";

          } catch (err) {
            // Hide loader on error
            if (typeof window.hideLoader === 'function') {
              window.hideLoader();
            } else if (typeof hideLoader === 'function') {
              hideLoader();
            }
            console.error("Fetch error:", err);
            if (statusText) statusText.innerText = "Cannot reach backend ❌";
          }
        };

      } catch (err) {
        console.error("Microphone error:", err);
        alert("Microphone permission denied!");
      }
    });
  }
  const text = json.text || json.subtitle || json.reply;

console.log("Subtitle text:", text);

if (text) {
  const bar = document.getElementById("subtitleBar");
  if (bar) {
    bar.innerHTML = text;
    bar.style.display = "block";
  }
}

  /* ================= AUDIO PLAYER ================= */
  if (audioPlayer && playBtn) {
    playBtn.addEventListener("click", () => {
      if (audioPlayer.paused) {
        audioPlayer.play();
        playBtn.textContent = "❚❚";
      } else {
        audioPlayer.pause();
        playBtn.textContent = "▶";
      }
    });

    audioPlayer.addEventListener("timeupdate", () => {
      if (!audioPlayer.duration) return;
      const percent = (audioPlayer.currentTime / audioPlayer.duration) * 100;
      if (progress) progress.style.width = percent + "%";
      if (timeText) {
        const mins = Math.floor(audioPlayer.currentTime / 60);
        const secs = Math.floor(audioPlayer.currentTime % 60).toString().padStart(2, "0");
        timeText.textContent = `${mins}:${secs}`;
      }
    });

    audioPlayer.addEventListener("ended", () => {
      playBtn.textContent = "▶";
      if (progress) progress.style.width = "0%";
    });
  }

}); // end DOMContentLoaded

/* ================= THEME TOGGLE FUNCTION ================= */
function toggleTheme() {
  if (document.body.classList.contains('dark-theme')) {
    document.body.classList.remove('dark-theme');
    document.body.classList.add('light-theme');
    localStorage.setItem('theme', 'light');
    const btn = document.getElementById('themeToggleBtn');
    if (btn) btn.textContent = '🌙';
  } else if (document.body.classList.contains('light-theme')) {
    document.body.classList.remove('light-theme');
    document.body.classList.add('dark-theme');
    localStorage.setItem('theme', 'dark');
    const btn = document.getElementById('themeToggleBtn');
    if (btn) btn.textContent = '☀️';
  } else {
    // Default to dark theme
    document.body.classList.add('dark-theme');
    localStorage.setItem('theme', 'dark');
    const btn = document.getElementById('themeToggleBtn');
    if (btn) btn.textContent = '☀️';
  }
}

/* ================= LOGOUT FUNCTION ================= */
function logout() {
  localStorage.clear();
  window.location.href = "login.html";
}

// Apply saved theme on page load
const savedTheme = localStorage.getItem('theme');
if (savedTheme === 'light') {
  document.body.classList.add('light-theme');
  document.body.classList.remove('dark-theme');
  const btn = document.getElementById('themeToggleBtn');
  if (btn) btn.textContent = '🌙';
} else {
  document.body.classList.add('dark-theme');
  document.body.classList.remove('light-theme');
  const btn = document.getElementById('themeToggleBtn');
  if (btn) btn.textContent = '☀️';
}