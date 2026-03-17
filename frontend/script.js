document.addEventListener("DOMContentLoaded", () => {

  const BACKEND = "http://127.0.0.1:8000";

  /* ================= PROFILE SECTION ================= */

  const nameEl = document.getElementById("name");
  const phoneEl = document.getElementById("phone-display");
  const langEl = document.getElementById("language");

  if (nameEl && phoneEl && langEl) {
    nameEl.innerText = localStorage.getItem("name") || "Unknown";
    phoneEl.innerText = localStorage.getItem("phone") || "Not available";
    langEl.innerText = localStorage.getItem("lang") || "Not set";
  }

  /* ================= LOGIN ================= */

  const loginBtn = document.getElementById("loginBtn");

  if (loginBtn) {
    loginBtn.addEventListener("click", async () => {

      const phone = document.getElementById("phone")?.value.trim();
      const password = document.getElementById("password")?.value.trim();
      const msg = document.getElementById("msg");

      if (!phone || !password) {
        msg.innerText = "Enter phone number & password";
        return;
      }

      try {
        const formData = new FormData();
        formData.append("phone", phone);
        formData.append("password", password);

        const res = await fetch(`${BACKEND}/login`, { method: "POST", body: formData });
        const data = await res.json();

        if (data.status === "not_found")        { msg.innerText = "User not found. Register first."; return; }
        if (data.status === "invalid_password") { msg.innerText = "Incorrect password"; return; }
        if (data.status !== "success")          { msg.innerText = "Login failed"; return; }

        localStorage.setItem("patient_id", data.patient.id);
        localStorage.setItem("lang", data.patient.preferred_language || "en");

        window.location.href = "indexx.html";

      } catch (err) {
        msg.innerText = "Cannot reach backend";
        console.error(err);
      }
    });
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

        const res = await fetch(`${BACKEND}/register`, { method: "POST", body: formData });
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
      window.location.href = "admin/admin_dashboard.html";
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

  let mediaRecorder;
  let audioChunks = [];

  if (recordBtn) {
    recordBtn.addEventListener("click", async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
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

          try {
            const res = await fetch(`${BACKEND}/process-audio`, { method: "POST", body: formData });

            if (!res.ok) {
              if (statusText) statusText.innerText = "Backend error ❌";
              return;
            }

            const audioData = await res.blob();
            const url = URL.createObjectURL(audioData);

            if (audioPlayer) {
              audioPlayer.src = url;
              audioPlayer.load();
              audioPlayer.play();
              if (playBtn) playBtn.textContent = "❚❚";
            }

            if (statusText) statusText.innerText = "Response received ✅";

          } catch {
            if (statusText) statusText.innerText = "Cannot reach backend ❌";
          }
        };

      } catch {
        alert("Microphone permission denied!");
      }
    });
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

});