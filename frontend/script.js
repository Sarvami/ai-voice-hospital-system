const micBtn = document.getElementById("micBtn");
const statusText = document.getElementById("status");
const player = document.getElementById("audioPlayer");

let recorder;
let chunks = [];

micBtn.onclick = async () => {

    // Ask mic permission
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    recorder = new MediaRecorder(stream);
    chunks = [];

    recorder.start();
    statusText.innerText = "Listening...";

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
