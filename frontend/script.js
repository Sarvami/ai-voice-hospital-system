const recordBtn = document.getElementById("recordBtn");
const statusText = document.getElementById("status");
const audioPlayer = document.getElementById("audioPlayer");

let mediaRecorder;
let audioChunks = [];

recordBtn.onclick = async () => {
    // 1. Ask for microphone access
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    // 2. Create recorder
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];

    mediaRecorder.start();
    statusText.innerText = "Listening...";

    // 3. Collect audio data
    mediaRecorder.ondataavailable = event => {
        audioChunks.push(event.data);
    };

    // 4. Stop after 5 seconds
    setTimeout(() => {
        mediaRecorder.stop();
        statusText.innerText = "Processing...";
    }, 5000);

    // 5. When recording stops
    mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: "audio/wav" });

        const formData = new FormData();
        formData.append("audio", audioBlob, "recording.wav");

        // 6. Send to backend
        const response = await fetch("http://127.0.0.1:8000/process-audio", {
            method: "POST",
            body: formData
        });

        // 7. Get audio reply
        const responseAudio = await response.blob();
        const audioUrl = URL.createObjectURL(responseAudio);

        audioPlayer.src = audioUrl;
        audioPlayer.play();

        statusText.innerText = "Response received";
    };
};