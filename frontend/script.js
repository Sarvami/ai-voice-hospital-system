document.addEventListener("DOMContentLoaded", () => {

<<<<<<< HEAD
  /* ---------------- LOGIN ---------------- */

  const loginBtn = document.getElementById("loginBtn");

  if (loginBtn) {
    loginBtn.addEventListener("click", async () => {

      const emailInput = document.getElementById("email");
      const passwordInput = document.getElementById("password");
      const msg = document.getElementById("msg");

      const email = emailInput?.value.trim();
      const password = passwordInput?.value.trim();

      if (!email || !password) {
        msg.innerText = "Enter email & password";
        return;
      }

      try {
        const res = await fetch("http://127.0.0.1:8000/login", {
=======
  const recordBtn = document.getElementById("recordBtn");
  const statusText = document.getElementById("status");
  const audioPlayer = document.getElementById("audioPlayer");

  let mediaRecorder;
  let audioChunks = [];

  // ❗ No default language
  let selectedLang = null;

  /* ---------------- LANGUAGE BUTTONS ---------------- */

  document.querySelectorAll(".bubble").forEach(btn => {

    btn.addEventListener("click", () => {

      // Remove old active
      document.querySelectorAll(".bubble")
        .forEach(b => b.classList.remove("active"));

      // Set new active
      btn.classList.add("active");

      selectedLang = btn.dataset.lang;

      statusText.innerText = "Language selected ✔";
    });

  });


  /* ---------------- MIC BUTTON ---------------- */

  recordBtn.addEventListener("click", async () => {

    // 🚨 If no language selected
    if (!selectedLang) {
      alert("Please select a language first!");
      return;
    }

    try {

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      mediaRecorder = new MediaRecorder(stream);
      audioChunks = [];

      mediaRecorder.start();
      statusText.innerText = "Listening... 🎙️";

      mediaRecorder.ondataavailable = e => {
        audioChunks.push(e.data);
      };

      setTimeout(() => {
        mediaRecorder.stop();
        statusText.innerText = "Processing...";
      }, 5000);

      mediaRecorder.onstop = async () => {

        const audioBlob = new Blob(audioChunks, { type: "audio/wav" });

        const formData = new FormData();
        formData.append("audio", audioBlob, "recording.wav");
        formData.append("lang", selectedLang);

        const response = await fetch("http://127.0.0.1:8000/process-audio", {
>>>>>>> 45bdcb2fe3304141c51d2bf0a38ae81845c0e14e
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password })
        });

<<<<<<< HEAD
        // 🔴 backend not reachable
        if (!res.ok) {
          msg.innerText = "Backend not reachable";
          return;
        }

        const data = await res.json();

        if (!data.success) {
          msg.innerText = "Invalid email or password";
          return;
        }

        // ✅ save user
        localStorage.setItem("user", JSON.stringify(data.user));

        // ✅ go to profile
        window.location.href = "profile.html";

      } catch (err) {
        msg.innerText = "Server not running";
        console.error(err);
      }
    });
  }

  /* ---------------- PROFILE ---------------- */

  const nameEl = document.getElementById("name");
  const emailEl = document.getElementById("emailDisplay"); // ⚠️ changed id

  if (nameEl && emailEl) {
    const user = JSON.parse(localStorage.getItem("user"));

    // 🔴 not logged in → go back
    if (!user) {
      window.location.href = "login.html";
      return;
    }

    // ✅ show user data
    nameEl.innerText = user.name ?? "Unknown";
    emailEl.innerText = user.email ?? "Unknown";
  }

  /* ---------------- LOGOUT ---------------- */

  const logoutBtn = document.getElementById("logoutBtn");

  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
      localStorage.removeItem("user");
      window.location.href = "login.html";
    });
  }
=======
        const responseAudio = await response.blob();

        const audioUrl = URL.createObjectURL(responseAudio);

        audioPlayer.src = audioUrl;
        audioPlayer.play();

        statusText.innerText = "Response received ✅";
      };

    } catch (err) {
      alert("Microphone permission denied!");
      console.error(err);
    }

  });
>>>>>>> 45bdcb2fe3304141c51d2bf0a38ae81845c0e14e

});
