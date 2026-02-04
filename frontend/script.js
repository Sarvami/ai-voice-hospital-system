console.log("Assistant script loaded");

// Elements
const recordBtn = document.getElementById("recordBtn"); // Ensure your HTML mic button has this ID
const statusText = document.getElementById("status");
const audioPlayer = document.getElementById("audioPlayer");

let mediaRecorder;
let audioChunks = [];
let selectedLanguage = "hi"; // Default to Hindi

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
    statusText.innerText = `Ready for ${btn.innerText}`;
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
    recordBtn.classList.add("recording-pulse"); // Add a CSS animation class if you have one

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
      // Create blob from chunks
      const audioBlob = new Blob(audioChunks, { type: "audio/webm" });

      // Prepare data for Backend
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

        // Play the response
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