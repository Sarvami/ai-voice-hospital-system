/* ── CONSTANTS & GLOBAL STATE ── */
const BACKEND = "http://127.0.0.1:8000";
let selectedLang = localStorage.getItem("lang") || "hi";
let captionHistory = [];
let mediaRecorder = null;
let audioChunks = [];
let pendingIntent = null;
let pendingDoctorId = null;

const UI_TEXT = {
  en: {
    welcome: "Hello! I'm your AI hospital assistant. Tap the microphone and tell me how I can help you today.",
    langSwitched: lang => `Language switched to ${lang}`,
    selectDate: "Please select your preferred appointment date from the calendar.",
    dateCancelled: "Date selection was cancelled.",
    selectRegion: "Please select your preferred region from the list.",
    regionCancelled: "Region selection was cancelled.",
    regionSet: region => `Region set to: ${region}`,
    dateSelected: date => `Selected date: ${date}`,
    regionSelected: region => `Selected region: ${region}`,
    dateError: "Sorry, there was an error setting the date.",
    regionError: "Sorry, there was an error setting the region.",
    serverError: "Sorry, there was an error processing your request.",
    connectError: "Sorry, I'm having trouble connecting to the server.",
  },
  hi: {
    welcome: "नमस्ते! मैं आपका AI अस्पताल सहायक हूँ। माइक्रोफोन दबाएं और बताएं मैं आपकी कैसे मदद कर सकता हूँ।",
    langSwitched: lang => `भाषा बदली: ${lang}`,
    selectDate: "कृपया कैलेंडर से अपनी पसंदीदा तारीख चुनें",
    dateCancelled: "तारीख चयन रद्द किया गया।",
    selectRegion: "कृपया सूची से अपना क्षेत्र चुनें",
    regionCancelled: "क्षेत्र चयन रद्द किया गया।",
    regionSet: region => `क्षेत्र सेट हुआ: ${region}`,
    dateSelected: date => `चुनी गई तारीख: ${date}`,
    regionSelected: region => `चुना गया क्षेत्र: ${region}`,
    dateError: "क्षमा करें, तारीख सेट करने में त्रुटि हुई।",
    regionError: "क्षमा करें, क्षेत्र सेट करने में त्रुटि हुई।",
    serverError: "क्षमा करें, आपका अनुरोध प्रोसेस करने में त्रुटि हुई।",
    connectError: "क्षमा करें, सर्वर से कनेक्ट करने में समस्या है।",
  },
  mr: {
    welcome: "नमस्कार! मी तुमचा AI रुग्णालय सहाय्यक आहे। मायक्रोफोन दाबा आणि सांगा मी तुम्हाला कशी मदत करू शकतो।",
    langSwitched: lang => `भाषा बदलली: ${lang}`,
    selectDate: "कृपया कॅलेंडरमधून तुमची पसंतीची तारीख निवडा",
    dateCancelled: "तारीख निवड रद्द केली.",
    selectRegion: "कृपया यादीतून तुमचा प्रदेश निवडा",
    regionCancelled: "प्रदेश निवड रद्द केली.",
    regionSet: region => `प्रदेश सेट झाला: ${region}`,
    dateSelected: date => `निवडलेली तारीख: ${date}`,
    regionSelected: region => `निवडलेला प्रदेश: ${region}`,
    dateError: "माफ करा, तारीख सेट करताना त्रुटी आली.",
    regionError: "माफ करा, प्रदेश सेट करताना त्रुटी आली.",
    serverError: "माफ करा, तुमची विनंती प्रक्रिया करताना त्रुटी आली.",
    connectError: "माफ करा, सर्व्हरशी कनेक्ट करण्यात समस्या आहे.",
  }
};

/* ── UTILITIES ── */
function t(key, ...args) {
  const lang = selectedLang || 'en';
  const entry = (UI_TEXT[lang] || UI_TEXT['en'])[key];
  return typeof entry === 'function' ? entry(...args) : entry;
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/[&<>]/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[m]));
}

function addCaptionToHistory(text, type) {
  if (!text) return;
  const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  captionHistory.push({ text, type, time });
  if (captionHistory.length > 15) captionHistory.shift();
  renderCaptions();
}

function renderCaptions() {
  const captionContainer = document.getElementById("captionContainer");
  const subtitleBar = document.getElementById("subtitleBar");
  if (!captionContainer) return;
  captionContainer.innerHTML = '';
  captionHistory.forEach(msg => {
    const div = document.createElement('div');
    div.className = msg.type === 'user' ? 'caption-user' : 'caption-ai';
    div.innerHTML = `<span class="caption-time">${msg.time}</span> ${escapeHtml(msg.text)}`;
    if (msg.type === 'ai' && selectedLang !== 'en') {
      const btn = document.createElement('button');
      btn.className = 'translate-btn';
      btn.textContent = 'See translation';
      btn.onclick = async () => {
        btn.textContent = 'Translating...';
        btn.disabled = true;
        try {
          const res = await fetch(`${BACKEND}/translate-text`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: msg.text, target_lang: 'en' })
          });
          const data = await res.json();
          if (data.success) {
            const transDiv = document.createElement('div');
            transDiv.className = 'translation-text';
            transDiv.textContent = '🇬🇧 ' + data.translation;
            div.appendChild(transDiv);
            btn.remove();
          } else btn.textContent = 'Translation failed';
        } catch (e) { btn.textContent = 'Translation failed'; }
        btn.disabled = false;
      };
      div.appendChild(btn);
    }
    captionContainer.appendChild(div);
  });
  if (subtitleBar) subtitleBar.scrollTop = subtitleBar.scrollHeight;
}

/* ── DOM INITIALIZATION ── */
document.addEventListener("DOMContentLoaded", () => {
  // Profiles
  updateProfileInfo();

  // Auth Guard
  if (document.getElementById("recordBtn") && !localStorage.getItem("patient_id")) {
    window.location.href = "login.html";
    return;
  }

  // Language Bubbles
  document.querySelectorAll(".bubble").forEach(btn => {
    if (btn.dataset.lang === selectedLang) btn.classList.add("active");
    btn.addEventListener("click", () => {
      document.querySelectorAll(".bubble").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      selectedLang = btn.dataset.lang;
      localStorage.setItem("lang", selectedLang);
      addCaptionToHistory(t('langSwitched', selectedLang.toUpperCase()), 'ai');
    });
  });

  // Theme
  const savedTheme = localStorage.getItem("theme") || "dark";
  document.body.classList.toggle("light-theme", savedTheme === "light");
  document.body.classList.toggle("dark-theme", savedTheme !== "light");
  const themeBtn = document.getElementById("themeToggleBtn");
  if (themeBtn) themeBtn.textContent = savedTheme === "light" ? "🌙" : "☀️";

  // Welcome
  setTimeout(() => addCaptionToHistory(t('welcome'), 'ai'), 500);

  // Setup Event Listeners
  setupEventListeners();

  // Initialize region
  const initialRegion = localStorage.getItem('region');
  if (initialRegion) setTimeout(() => updateRegion(initialRegion), 1000);
});

function setupEventListeners() {
  const recordBtn = document.getElementById("recordBtn");
  const audioPlayer = document.getElementById("audioPlayer");
  const playBtn = document.getElementById("playBtn");
  const progress = document.getElementById("progress");

  if (recordBtn) recordBtn.addEventListener("click", handleMicClick);

  if (audioPlayer && playBtn) {
    playBtn.addEventListener("click", () => {
      if (audioPlayer.paused) { audioPlayer.play(); playBtn.textContent = "❚❚"; }
      else { audioPlayer.pause(); playBtn.textContent = "▶"; }
    });
    audioPlayer.addEventListener("timeupdate", () => {
      if (!audioPlayer.duration) return;
      const pct = (audioPlayer.currentTime / audioPlayer.duration) * 100;
      if (progress) progress.style.width = pct + "%";
    });
    audioPlayer.addEventListener("ended", () => {
      playBtn.textContent = "▶";
      if (progress) progress.style.width = "0%";
    });
  }

  const profileIcon = document.getElementById("profileIcon");
  const profileDropdown = document.getElementById("profileDropdown");
  if (profileIcon && profileDropdown) {
    profileIcon.onclick = (e) => { e.stopPropagation(); profileDropdown.classList.toggle("show"); };
  }
}

async function handleMicClick() {
  const recordBtn = document.getElementById("recordBtn");
  const statusText = document.getElementById("status");
  const audioPlayer = document.getElementById("audioPlayer");

  if (mediaRecorder && mediaRecorder.state === "recording") {
    mediaRecorder.stop();
    return;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const source = audioContext.createMediaStreamSource(stream);
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 256;
    source.connect(analyser);
    const dataArray = new Uint8Array(analyser.frequencyBinCount);

    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];
    mediaRecorder.start();
    if (statusText) statusText.innerText = "🎙️ Listening...";
    recordBtn.classList.add("recording");

    let lastSpeakTime = Date.now();
    const checkSilence = () => {
      if (!mediaRecorder || mediaRecorder.state !== "recording") return;
      analyser.getByteFrequencyData(dataArray);
      let average = dataArray.reduce((a,b)=>a+b,0) / dataArray.length;
      if (average > 10) lastSpeakTime = Date.now();
      if (Date.now() - lastSpeakTime > 2000) mediaRecorder.stop();
      else requestAnimationFrame(checkSilence);
    };
    requestAnimationFrame(checkSilence);

    mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach(t => t.stop());
      audioContext.close();
      if (statusText) statusText.innerText = "⏳ Processing...";
      recordBtn.classList.remove("recording");

      const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
      const formData = new FormData();
      formData.append("audio", audioBlob, "recording.wav");
      formData.append("lang", selectedLang);
      formData.append("patient_id", localStorage.getItem("patient_id"));

      showLoader();
      try {
        const res = await fetch(`${BACKEND}/process-audio`, { method: "POST", body: formData });
        hideLoader();
        const json = await res.json();
        
        const aiText = json.reply_in_lang || json.text;
        if (aiText) addCaptionToHistory(aiText, 'ai');

        if (json.audio_url && audioPlayer) {
          audioPlayer.src = json.audio_url.startsWith('http') ? json.audio_url : `${BACKEND}${json.audio_url}`;
          audioPlayer.play();
        }

        if (json.booked) showSuccessPopup("Appointment booked!");

        if (json.intent === "ask_date") {
           const date = await openCalendarPopup();
           if (date) selectDate(date, json.doctor_id);
        } else if (json.intent === "ask_region") {
           const reg = await openRegionPopup();
           if (reg) selectRegion(reg);
        }
      } catch (err) { hideLoader(); console.error(err); }
    };
  } catch (err) { alert("Mic error: " + err); }
}

/* ── GLOBAL HANDLERS ── */
async function updateRegion(region) {
  if (!region) return;
  localStorage.setItem('region', region);
  const label = document.getElementById('selectedRegion');
  if (label) label.textContent = region;

  try {
    const res = await fetch(`${BACKEND}/set-region`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        patient_id: localStorage.getItem('patient_id') || 'user1',
        region: region,
        lang: selectedLang
      })
    });
    const data = await res.json();
    if (data.text) addCaptionToHistory(data.text, 'ai');
    if (data.audio_url) {
      const player = document.getElementById("audioPlayer");
      player.src = data.audio_url.startsWith('http') ? data.audio_url : `${BACKEND}${data.audio_url}`;
      player.play();
    }
  } catch (e) { console.error(e); }
}

function toggleRegionDropdown(e) {
  if (e) e.stopPropagation();
  document.getElementById('regionDropdown')?.classList.toggle('active');
}

function selectRegion(region) {
  document.getElementById('regionDropdown')?.classList.remove('active');
  updateRegion(region);
}

function selectDate(date, doctorId) {
  showLoader();
  fetch(`${BACKEND}/set-appointment-date`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      patient_id: localStorage.getItem("patient_id"),
      date: date,
      doctor_id: doctorId,
      lang: selectedLang
    })
  }).then(r => r.json()).then(data => {
    hideLoader();
    if (data.text) addCaptionToHistory(data.text, 'ai');
    if (data.audio_url) {
       const p = document.getElementById("audioPlayer");
       p.src = data.audio_url.startsWith('http') ? data.audio_url : `${BACKEND}${data.audio_url}`;
       p.play();
    }
  }).catch(e => hideLoader());
}

function toggleTheme() {
  const isLight = document.body.classList.toggle("light-theme");
  document.body.classList.toggle("dark-theme", !isLight);
  localStorage.setItem("theme", isLight ? "light" : "dark");
  const btn = document.getElementById("themeToggleBtn");
  if (btn) btn.textContent = isLight ? "🌙" : "☀️";
}

function showLoader() { document.getElementById("loaderOverlay")?.classList.add("show"); }
function hideLoader() { document.getElementById("loaderOverlay")?.classList.remove("show"); }

function showSuccessPopup(msg) {
  const el = document.getElementById("successMsg");
  if (el) el.textContent = msg;
  document.getElementById("successPopup")?.classList.add("show");
  setTimeout(() => document.getElementById("successPopup")?.classList.remove("show"), 3000);
}

/* ── CALENDAR LOGIC ── */
let calPopupDate = new Date();
let calPopupResolve = null;

function openCalendarPopup() {
  return new Promise(resolve => {
    calPopupResolve = resolve;
    calPopupDate = new Date();
    renderCalPopup();
    document.getElementById("calendarPopup").classList.add("show");
  });
}

function calChangeMonth(dir) {
  calPopupDate.setMonth(calPopupDate.getMonth() + dir);
  renderCalPopup();
}

function renderCalPopup() {
  const year = calPopupDate.getFullYear();
  const month = calPopupDate.getMonth();
  const today = new Date(); today.setHours(0,0,0,0);
  
  const label = document.getElementById("calPopupLabel");
  if (label) label.textContent = calPopupDate.toLocaleDateString("en-IN", { month: "long", year: "numeric" });

  const grid = document.getElementById("calPopupGrid");
  if (!grid) return;
  grid.innerHTML = "";
  
  ["Su","Mo","Tu","We","Th","Fr","Sa"].forEach(d => {
    const h = document.createElement("div"); h.className="ch"; h.textContent=d; grid.appendChild(h);
  });

  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  for(let i=0; i<firstDay; i++) grid.appendChild(document.createElement("div"));

  for(let d=1; d<=daysInMonth; d++) {
    const cell = document.createElement("div"); cell.className="cd"; cell.textContent=d;
    const thisDate = new Date(year, month, d);
    if (thisDate < today) cell.classList.add("disabled");
    else {
      cell.onclick = () => {
        const dateStr = `${year}-${String(month+1).padStart(2,"0")}-${String(d).padStart(2,"0")}`;
        document.getElementById("calendarPopup").classList.remove("show");
        if (calPopupResolve) calPopupResolve(dateStr);
      };
    }
    grid.appendChild(cell);
  }
}

/* ── REGION POPUP ── */
let regPopupResolve = null;
function openRegionPopup() {
  return new Promise(resolve => {
    regPopupResolve = resolve;
    document.getElementById("regionPopup").classList.add("show");
  });
}
function confirmRegion() {
  const reg = document.getElementById("regionSelect").value;
  if (!reg) return;
  document.getElementById("regionPopup").classList.remove("show");
  if (regPopupResolve) regPopupResolve(reg);
}

// Global click-away
window.addEventListener('click', (e) => {
  const rd = document.getElementById('regionDropdown');
  if (rd && !rd.contains(e.target)) rd.classList.remove('active');
  const pd = document.getElementById("profileDropdown");
  const pi = document.getElementById("profileIcon");
  if (pd && pi && !pi.contains(e.target) && !pd.contains(e.target)) pd.classList.remove("show");
});

function updateProfileInfo() {
  const userData = JSON.parse(localStorage.getItem("user") || "{}");
  const name = localStorage.getItem("name") || userData.name || "Guest";
  const phone = localStorage.getItem("phone") || userData.phone || "";

  const dropdownName  = document.getElementById("dropdownName");
  const dropdownEmail = document.getElementById("dropdownEmail");
  const profileIcon   = document.getElementById("profileIcon");
  const dropdownAvatar = document.getElementById("dropdownAvatar");

  if (dropdownName)  dropdownName.textContent  = name;
  if (dropdownEmail) dropdownEmail.textContent = phone || (name !== "Guest" ? "Signed in" : "Not signed in");

  const initials = name !== 'Guest' ? name.charAt(0).toUpperCase() : '👤';
  if (profileIcon) profileIcon.textContent = initials;
  if (dropdownAvatar) dropdownAvatar.textContent = initials;
}

function logout() {
  localStorage.clear();
  window.location.href = 'login.html';
}

function closeSuccessPopup() {
  document.getElementById('successPopup')?.classList.remove('show');
}
