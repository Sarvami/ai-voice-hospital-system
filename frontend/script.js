<<<<<<< HEAD
console.log("script loaded");

const recordBtn = document.getElementById("recordBtn");
=======
const micBtn = document.getElementById("micBtn");
>>>>>>> 5043525029955964947ba698f6c45e0dd67c2f33
const statusText = document.getElementById("status");
const player = document.getElementById("audioPlayer");

<<<<<<< HEAD
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
=======
let recorder;
let chunks = [];

micBtn.onclick = async () => {

    // Ask mic permission
>>>>>>> 5043525029955964947ba698f6c45e0dd67c2f33
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    console.log("Mic permission granted");

<<<<<<< HEAD
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];
=======
    recorder = new MediaRecorder(stream);
    chunks = [];
>>>>>>> 5043525029955964947ba698f6c45e0dd67c2f33

    recorder.start();
    statusText.innerText = "Listening...";

<<<<<<< HEAD
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
=======
    recorder.ondataavailable = e => {
        chunks.push(e.data);
    };

    // Stop after 5 seconds
    setTimeout(() => {
        recorder.stop();
        statusText.innerText = "Processing...";
    }, 5000);

    recorder.onstop = async () => {

        const blob = new Blob(chunks, { type: "audio/wav" });

        const data = new FormData();
        data.append("audio", blob, "voice.wav");

        // Send to backend
        const res = await fetch("http://127.0.0.1:8000/process-audio", {
            method: "POST",
            body: data
        });

        if (!res.ok) {
            statusText.innerText = "Backend error";
            return;
        }

        const audio = await res.blob();
        const url = URL.createObjectURL(audio);

        // Play reply
        player.src = url;
        player.play();

        statusText.innerText = "Done";
    };
};
>>>>>>> 5043525029955964947ba698f6c45e0dd67c2f33
