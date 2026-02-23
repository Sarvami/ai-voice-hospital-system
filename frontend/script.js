document.addEventListener("DOMContentLoaded", () => {
// Prevent direct access to profile page
if (
  window.location.pathname.includes("profile.html") &&
  !localStorage.getItem("temp_phone")
) {
  window.location.href = "login.html";
}

  /* ================= LOGIN ================= */

  const loginBtn = document.getElementById("loginBtn");

  if (loginBtn) {
    loginBtn.addEventListener("click", async () => {
      console.log("Login button clicked");

      const phone = document.getElementById("phone")?.value.trim();
      const password = document.getElementById("password")?.value.trim();
      const msg = document.getElementById("msg");

      if (!phone || !password) {
        msg.innerText = "Enter  & phone and password";
        return;
      }

      try {
        
const formData = new FormData();
formData.append("phone", phone);
formData.append("password", password);

const res = await fetch("http://127.0.0.1:8000/login", {
  method: "POST",
  body: formData
});

        const data = await res.json();

        if (data.status === "not_found") {
  // user does not exist → go to profile creation
  localStorage.setItem("temp_phone", phone);
  window.location.href = "profile.html";
  return;
}

if (data.status === "invalid_password") {
  msg.innerText = "Incorrect password";
  return;
}

if (data.status !== "success") {
  msg.innerText = "Login failed";
  return;
}

        localStorage.setItem("patient_id", data.patient.id);
localStorage.setItem("lang", data.patient.preferred_language);

        // 🔥 go to MAIN voice page (not profile)
        window.location.href = "index.html";

      } catch (err) {
        msg.innerText = "Backend not running";
        console.error(err);
      }
    });
  }

  /* ================= PROFILE ================= */

  const nameEl = document.getElementById("name");
  const emailEl = document.getElementById("emailDisplay");

  if (nameEl && emailEl) {
    const user = JSON.parse(localStorage.getItem("user"));

    if (!user) {
      window.location.href = "login.html";
      return;
    }

    nameEl.innerText = user.name;
    emailEl.innerText = user.email;
  }

  /* ================= LOGOUT ================= */

  const logoutBtn = document.getElementById("logoutBtn");

  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
      localStorage.removeItem("user");
      window.location.href = "login.html";
    });
  }

  /* ================= VOICE ASSISTANT ================= */

  const recordBtn = document.getElementById("recordBtn");
  const statusText = document.getElementById("status");
  const audioPlayer = document.getElementById("audioPlayer");

  let mediaRecorder;
  let audioChunks = [];
  let selectedLang = "hi"; // default Hindi

  // language buttons
  document.querySelectorAll(".bubble").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".bubble").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      selectedLang = btn.dataset.lang;

      if (statusText) statusText.innerText = "Language selected ✔";
    });
  });

  // mic button
  if (recordBtn) {
    recordBtn.addEventListener("click", async () => {

      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.start();
        if (statusText) statusText.innerText = "Listening... 🎙️";

        mediaRecorder.ondataavailable = e => audioChunks.push(e.data);

        setTimeout(() => {
          mediaRecorder.stop();
          if (statusText) statusText.innerText = "Processing...";
        }, 5000);

        mediaRecorder.onstop = async () => {

          const audioBlob = new Blob(audioChunks, { type: "audio/wav" });

          const formData = new FormData();
          formData.append("audio", audioBlob, "recording.wav");
          formData.append("lang", selectedLang);
          formData.append("patient_id", localStorage.getItem("patient_id"));

          try {
            const res = await fetch("http://127.0.0.1:8000/process-audio", {
              method: "POST",
              body: formData
            });

            if (!res.ok) {
              if (statusText) statusText.innerText = "Backend error ❌";
              return;
            }

            const audioData = await res.blob();
            const url = URL.createObjectURL(audioData);

            if (audioPlayer) {
              audioPlayer.src = url;
              audioPlayer.play();
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

});
const audio = document.getElementById("audioPlayer");
const playBtn = document.getElementById("playBtn");
const progress = document.getElementById("progress");
const timeText = document.getElementById("time");

if (audio && playBtn && progress && timeText) {

  playBtn.addEventListener("click", () => {
    if (audio.paused) {
      audio.play();
      playBtn.textContent = "❚❚";
    } else {
      audio.pause();
      playBtn.textContent = "▶";
    }
  });

  audio.addEventListener("timeupdate", () => {
    const percent = (audio.currentTime / audio.duration) * 100;
    progress.style.width = percent + "%";

    const mins = Math.floor(audio.currentTime / 60);
    const secs = Math.floor(audio.currentTime % 60)
      .toString()
      .padStart(2, "0");

    timeText.textContent = `${mins}:${secs}`;
  });

  audio.addEventListener("ended", () => {
    playBtn.textContent = "▶";
    progress.style.width = "0%";
  });

}

/* ================= REGISTER (PROFILE PAGE) ================= */

const registerBtn = document.getElementById("registerBtn");

if (registerBtn) {
  registerBtn.addEventListener("click", async () => {
    console.log("Register button clicked");

    const name = document.getElementById("name")?.value.trim();
    const age = document.getElementById("age")?.value.trim();
    const gender = document.getElementById("gender")?.value;
    const password = document.getElementById("password")?.value.trim();
    const language = document.getElementById("language")?.value || "en";
    const phone = localStorage.getItem("temp_phone");
    const msg = document.getElementById("msg");

    if (!name || !age || !gender || !password || !phone) {
      msg.innerText = "Please fill all fields";
      msg.style.color = "red";
      return;
    }

    msg.innerText = "Creating account...";
    msg.style.color = "black";

    try {
      const formData = new FormData();
      formData.append("name", name);
      formData.append("age", age);
      formData.append("gender", gender);
      formData.append("phone", phone);
      formData.append("password", password);
      formData.append("language", language);

      const res = await fetch("http://127.0.0.1:8000/register", {
        method: "POST",
        body: formData
      });

      const data = await res.json();
      console.log("Register response:", data);

      if (data.status === "created") {
        msg.style.color = "green";
        msg.innerText = "Profile created successfully! Redirecting...";
        localStorage.removeItem("temp_phone");

        setTimeout(() => {
          window.location.href = "index.html";
        }, 1000);
      } else {
        msg.style.color = "red";
        msg.innerText = data.error || "Registration failed";
      }

    } catch (err) {
      console.error(err);
      msg.style.color = "red";
      msg.innerText = "Cannot reach backend";
    }
  });
}