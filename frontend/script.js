document.addEventListener("DOMContentLoaded", () => {

  /* ================= LOGIN ================= */

  const loginBtn = document.getElementById("loginBtn");

  if (loginBtn) {
    loginBtn.addEventListener("click", async () => {

      const email = document.getElementById("email")?.value.trim();
      const password = document.getElementById("password")?.value.trim();
      const msg = document.getElementById("msg");

      if (!email || !password) {
        msg.innerText = "Enter email & password";
        return;
      }

      try {
        const res = await fetch("http://127.0.0.1:8000/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password })
        });

        const data = await res.json();

        if (!data.success) {
          msg.innerText = "Invalid email or password";
          return;
        }

        localStorage.setItem("user", JSON.stringify(data.user));

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
