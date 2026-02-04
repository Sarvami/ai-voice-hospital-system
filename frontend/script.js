console.log("script loaded");

const recordBtn = document.getElementById("recordBtn");
const statusText = document.getElementById("status");
const audioPlayer = document.getElementById("audioPlayer");

let mediaRecorder;
let audioChunks = [];
let selectedLanguage = "hi";

/* ---------- LANGUAGE SELECTION ---------- */
document.querySelectorAll(".bubble").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".bubble").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    selectedLanguage = btn.dataset.lang;
    console.log("Language selected:", selectedLanguage);
  });
});

/* ---------- RECORD AUDIO ---------- */
recordBtn.addEventListener("click", async () => {
  console.log("MIC CLICKED");

  if (!navigator.mediaDevices || !window.MediaRecorder) {
    alert("Audio recording not supported in this browser");
    return;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    console.log("Mic permission granted");

    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];

    mediaRecorder.start();
    statusText.innerText = "Listening...";

    mediaRecorder.ondataavailable = event => {
      audioChunks.push(event.data);
    };

    setTimeout(() => {
      mediaRecorder.stop();
      statusText.innerText = "Processing...";
    }, 5000);

    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: "audio/webm" });

      const formData = new FormData();
      formData.append("audio", audioBlob, "recording.webm");
      formData.append("language", selectedLanguage);

      const response = await fetch("http://127.0.0.1:8000/process-audio", {
        method: "POST",
        body: formData
      });

      const responseAudio = await response.blob();
      const audioUrl = URL.createObjectURL(responseAudio);

      audioPlayer.src = audioUrl;
      audioPlayer.play();   // ✅ auto play

      statusText.innerText = "Response received";
    };

  } catch (err) {
    console.error(err);
    alert("Microphone access denied");
  }
});
