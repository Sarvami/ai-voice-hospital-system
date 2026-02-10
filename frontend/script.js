document.addEventListener("DOMContentLoaded", () => {

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
          method: "POST",
          body: formData
        });

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

});
