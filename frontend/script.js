document.addEventListener("DOMContentLoaded", () => {

  const BACKEND = "http://127.0.0.1:8000";

  const UI_TEXT = {
  en: {
    welcome: "Hello! I'm your AI hospital assistant. Tap the microphone and tell me how I can help you today.",
    langSwitched: lang => `Language switched to ${lang}`,
    selectDate: "Please select your preferred appointment date from the calendar",
    dateCancelled: "Date selection was cancelled.",
    selectRegion: "Please select your preferred region from the list",
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

function t(key, ...args) {
  const lang = selectedLang || 'en';
  const entry = (UI_TEXT[lang] || UI_TEXT['en'])[key];
  return typeof entry === 'function' ? entry(...args) : entry;
}

  /* ── PROFILE SECTION ── */
  const nameEl  = document.getElementById("name");
  const phoneEl = document.getElementById("phone-display");
  const langEl  = document.getElementById("language");
  if (nameEl)  nameEl.innerText  = localStorage.getItem("name")  || "Unknown";
  if (phoneEl) phoneEl.innerText = localStorage.getItem("phone") || "Not available";
  if (langEl)  langEl.innerText  = localStorage.getItem("lang")  || "Not set";

  /* ── REGISTER ── */
  const registerBtn = document.getElementById("registerBtn");
  if (registerBtn) {
    registerBtn.addEventListener("click", async () => {
      const name     = document.getElementById("reg-name")?.value.trim();
      const age      = document.getElementById("reg-age")?.value.trim();
      const gender   = document.getElementById("reg-gender")?.value;
      const phone    = document.getElementById("reg-phone")?.value.trim();
      const password = document.getElementById("reg-password")?.value.trim();
      const language = document.getElementById("reg-language")?.value;
      const msg      = document.getElementById("reg-msg");

      if (!name || !age || !gender || !phone || !password) {
        msg.className = "msg error";
        msg.innerText = "Please fill in all fields";
        return;
      }
      if (phone.replace(/\D/g, "").length < 10) {
        msg.className = "msg error";
        msg.innerText = "Enter a valid 10-digit phone number";
        return;
      }
      try {
        const formData = new FormData();
        formData.append("name", name);
        formData.append("age", age);
        formData.append("gender", gender);
        formData.append("phone", phone.replace(/\D/g, "").slice(0, 10));
        formData.append("password", password);
        formData.append("language", language);

        const res  = await fetch(`${BACKEND}/register`, { method: "POST", body: formData });
        const json = await res.json();
        alert("Backend returned: " + JSON.stringify(json));

        if (data.error) { msg.className = "msg error"; msg.innerText = data.error; return; }
        msg.className = "msg success";
        msg.innerText = "Account created! Redirecting to login...";
        setTimeout(() => window.location.href = "login.html", 1500);
      } catch (err) {
        msg.className = "msg error";
        msg.innerText = "Cannot reach backend";
      }
    });
  }

  /* ── LOGOUT BUTTON ── */
  const logoutBtn = document.getElementById("logoutBtn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
      localStorage.clear();
      window.location.href = "login.html";
    });
  }

  /* ── AUTH GUARD ── */
  if (document.getElementById("recordBtn")) {
    const patientId = localStorage.getItem("patient_id");
    if (!patientId) {
      window.location.href = "login.html";
      return;
    }
  }

  /* ── LANGUAGE SELECTION ── */
  let selectedLang = localStorage.getItem("lang") || "hi";

  document.querySelectorAll(".bubble").forEach(btn => {
    if (btn.dataset.lang === selectedLang) btn.classList.add("active");
    btn.addEventListener("click", () => {
      document.querySelectorAll(".bubble").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      selectedLang = btn.dataset.lang;
      localStorage.setItem("lang", selectedLang);
      const statusText = document.getElementById("status");
      if (statusText) statusText.innerText = "Language selected ✔";
      addCaptionToHistory(t('langSwitched', selectedLang.toUpperCase()), 'ai');
    });
  });

  /* ── ENHANCED SUBTITLE SYSTEM (with history) ── */
  let captionHistory = [];
  const captionContainer = document.getElementById("captionContainer");
  const subtitleBar = document.getElementById("subtitleBar");

  function addCaptionToHistory(text, type) {
    if (!text) return;
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    captionHistory.push({ text, type, time });
    // Keep last 15 messages for clean UI
    if (captionHistory.length > 15) captionHistory.shift();
    renderCaptions();
  }

  function renderCaptions() {
    if (!captionContainer) return;
    captionContainer.innerHTML = '';
    captionHistory.forEach(msg => {
  const div = document.createElement('div');
  div.className = msg.type === 'user' ? 'caption-user' : 'caption-ai';
  div.innerHTML = `<span class="caption-time">${msg.time}</span> ${escapeHtml(msg.text)}`;

  // Add translate button only for AI captions and non-English languages
  if (msg.type === 'ai' && selectedLang !== 'en') {
    const btn = document.createElement('button');
    btn.className = 'translate-btn';
    btn.textContent = 'See translation';
    btn.onclick = async () => {
      btn.textContent = 'Translating...';
      btn.disabled = true;
      try {
        const res = await fetch('https://api.anthropic.com/v1/messages', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            model: 'claude-sonnet-4-20250514',
            max_tokens: 200,
            messages: [{
              role: 'user',
              content: `Translate this to English. Reply with ONLY the translation, nothing else: "${msg.text}"`
            }]
          })
        });
        const data = await res.json();
        const translation = data.content?.[0]?.text || 'Could not translate';
        const transDiv = document.createElement('div');
        transDiv.className = 'translation-text';
        transDiv.textContent = '🇬🇧 ' + translation;
        div.appendChild(transDiv);
        btn.remove();
      } catch(e) {
  btn.textContent = 'Translation failed';
  btn.disabled = false;  // ← add this
}
    };
    div.appendChild(btn);
  }

  captionContainer.appendChild(div);
});
    // Auto-scroll to bottom
    if (subtitleBar) subtitleBar.scrollTop = subtitleBar.scrollHeight;
  }

  // Helper to escape HTML
  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>]/g, function(m) {
      if (m === '&') return '&amp;';
      if (m === '<') return '&lt;';
      if (m === '>') return '&gt;';
      return m;
    });
  }

  /* ── VOICE ASSISTANT ── */
  const recordBtn   = document.getElementById("recordBtn");
  const statusText  = document.getElementById("status");
  const audioPlayer = document.getElementById("audioPlayer");
  const playBtn     = document.getElementById("playBtn");
  const progress    = document.getElementById("progress");
  const timeText    = document.getElementById("time");
  
  let mediaRecorder;
  let audioChunks   = [];
  let pendingIntent = null;
  let pendingDoctorId = null;
  let recordingTimeout = null;

  if (recordBtn) {
    recordBtn.addEventListener("click", async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks   = [];
        mediaRecorder.start();

        if (statusText) statusText.innerText = "🎙️ Listening... Speak now!";
        recordBtn.classList.add("recording");

        // Clear previous timeout if exists
        if (recordingTimeout) clearTimeout(recordingTimeout);
        
        recordingTimeout = setTimeout(() => {
          if (mediaRecorder && mediaRecorder.state === "recording") {
            mediaRecorder.stop();
            stream.getTracks().forEach(t => t.stop());
            if (statusText) statusText.innerText = "⏳ Processing your request...";
            recordBtn.classList.remove("recording");
          }
        }, 5000);

        mediaRecorder.ondataavailable = e => audioChunks.push(e.data);

        mediaRecorder.onstop = async () => {
          if (recordingTimeout) clearTimeout(recordingTimeout);
          
          const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
          const formData  = new FormData();
          formData.append("audio", audioBlob, "recording.wav");
          formData.append("lang", selectedLang);
          formData.append("patient_id", localStorage.getItem("patient_id"));

          showLoader();

          try {
            const res = await fetch(`${BACKEND}/process-audio`, { method: "POST", body: formData });
            hideLoader();

            if (!res.ok) {
              if (statusText) statusText.innerText = "❌ Backend error";
              addCaptionToHistory(t('regionError'), 'ai');
              return;
            }

            const contentType = res.headers.get("content-type") || "";

            if (contentType.includes("application/json")) {
              const json = await res.json();
              
              // DEBUG: Log the response
              console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
              console.log("BACKEND RESPONSE:", json);
              console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");

          

/* Show AI reply in THEIR language (GREEN) */
const aiText = json.reply_in_lang || json.text || json.subtitle || json.reply;
if (aiText) {
  addCaptionToHistory(aiText, 'ai');
}

              /* Handle date request */
              if (aiText && (
  aiText.toLowerCase().includes("what date") ||
  aiText.toLowerCase().includes("which date") ||
  aiText.toLowerCase().includes("pick a date") ||
  aiText.toLowerCase().includes("select date") ||
  aiText.includes("तारीख") ||
  aiText.includes("दिनांक") ||
  aiText.includes("दिवस") ||
  json.intent === "ask_date"
)){
                if (json.audio_url && audioPlayer) {
        audioPlayer.src = json.audio_url;
        audioPlayer.load();
        audioPlayer.play();
        if (playBtn) playBtn.textContent = "❚❚";
    }
                pendingIntent = "date";
                if (json.doctor_id) pendingDoctorId = json.doctor_id;

                addCaptionToHistory(t('selectDate'), 'ai');
                
                const selectedDate = await openCalendarPopup();
                if (selectedDate) {
                  addCaptionToHistory(t('dateSelected', selectedDate), 'user');
                  showLoader();
                  try {
                    const dateRes = await fetch(`${BACKEND}/set-appointment-date`, {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({
                        patient_id: localStorage.getItem("patient_id"),
                        date: selectedDate,
                        doctor_id: pendingDoctorId,
                        lang: selectedLang
                      })
                    });
                    const dateResult = await dateRes.json();
                    if (dateResult.text) {
                      addCaptionToHistory(dateResult.text, 'ai');
                    }
                    if (dateResult.audio_url && audioPlayer) {
    const fullUrl = dateResult.audio_url.startsWith("http") 
        ? dateResult.audio_url 
        : `http://127.0.0.1:8000${dateResult.audio_url}`;
    audioPlayer.src = fullUrl;
    audioPlayer.load();
    audioPlayer.play();
    if (playBtn) playBtn.textContent = "❚❚";
}
                    if (dateResult.booked) {
                      showSuccessPopup(dateResult.success_message || "Your appointment has been successfully booked!");
                    }
                  } catch(e) { 
                    console.error("Date error:", e);
                    addCaptionToHistory(t('serverError'), 'ai');
                  }
                  finally { hideLoader(); }
                } else {
                  addCaptionToHistory(t('dateCancelled'), 'ai');
                }
                pendingIntent = null;
                return;
              }

              /* Handle region request */
              if (aiText && (
  aiText.toLowerCase().includes("region") ||
  aiText.toLowerCase().includes("location") ||
  aiText.toLowerCase().includes("area") ||
  aiText.includes("क्षेत्र") ||
  aiText.includes("इलाका") ||
  aiText.includes("प्रदेश") ||
  json.intent === "ask_region"
)) {
                pendingIntent = "region";
                if (json.doctor_id) pendingDoctorId = json.doctor_id;

                addCaptionToHistory(t('selectRegion'), 'ai');
                
                const selectedRegion = await openRegionPopup();
                if (selectedRegion) {
                  addCaptionToHistory(t('regionSelected', selectedRegion), 'user');
                  showLoader();
                  try {
                    const regRes = await fetch(`${BACKEND}/set-region`, {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({
                        patient_id: localStorage.getItem("patient_id"),
                        region: selectedRegion,
                        doctor_id: pendingDoctorId,
                        lang: selectedLang
                      })
                    });
                    const regResult = await regRes.json();
                    if (regResult.text) {
                      addCaptionToHistory(regResult.text, 'ai');
                    }
                    if (regResult.audio_url && audioPlayer) {
                      audioPlayer.src = regResult.audio_url;
                      audioPlayer.load();
                      audioPlayer.play();
                      if (playBtn) playBtn.textContent = "❚❚";
                    }
                    if (regResult.booked) {
                      showSuccessPopup(regResult.success_message || "Your appointment has been successfully booked!");
                    }
                  } catch(e) { 
                    console.error("Region error:", e);
                    addCaptionToHistory(t('dateError'), 'ai');
                  }
                  finally { hideLoader(); }
                } else {
                  addCaptionToHistory(t('regionCancelled'), 'ai');
                }
                pendingIntent = null;
                return;
              }

              /* Show success popup if appointment booked */
              if (json.booked) {
                showSuccessPopup(json.success_message || "Your appointment has been successfully booked!");
              }

              /* Play audio */
              if (json.audio_url && audioPlayer) {
                audioPlayer.src = json.audio_url;
                audioPlayer.load();
                audioPlayer.play();
                if (playBtn) playBtn.textContent = "❚❚";
              }

            } else {
              /* Raw audio blob */
              const audioData = await res.blob();
              const url = URL.createObjectURL(audioData);
              if (audioPlayer) {
                audioPlayer.src = url;
                audioPlayer.load();
                audioPlayer.play();
                if (playBtn) playBtn.textContent = "❚❚";
              }
            }

            if (statusText) statusText.innerText = "✅ Response received";

          } catch (err) {
            hideLoader();
            console.error("Fetch error:", err);
            if (statusText) statusText.innerText = "❌ Cannot reach backend";
            addCaptionToHistory("Sorry, I'm having trouble connecting to the server.", 'ai');
          }
        };

      } catch (err) {
        console.error("Mic error:", err);
        alert("Microphone permission denied! Please allow microphone access and try again.");
        if (statusText) statusText.innerText = "❌ Microphone access denied";
      }
    });
  }

  /* ── AUDIO PLAYER ── */
  if (audioPlayer && playBtn) {
    playBtn.addEventListener("click", () => {
      if (audioPlayer.paused) { 
        audioPlayer.play(); 
        playBtn.textContent = "❚❚"; 
      } else { 
        audioPlayer.pause(); 
        playBtn.textContent = "▶"; 
      }
    });

    audioPlayer.addEventListener("timeupdate", () => {
      if (!audioPlayer.duration) return;
      const pct = (audioPlayer.currentTime / audioPlayer.duration) * 100;
      if (progress) progress.style.width = pct + "%";
      if (timeText) {
        const m = Math.floor(audioPlayer.currentTime / 60);
        const s = Math.floor(audioPlayer.currentTime % 60).toString().padStart(2, "0");
        timeText.textContent = `${m}:${s}`;
      }
    });

    audioPlayer.addEventListener("ended", () => {
      playBtn.textContent = "▶";
      if (progress) progress.style.width = "0%";
    });
  }

  /* ── PROFILE DROPDOWN ── */
  const profileIcon     = document.getElementById("profileIcon");
  const profileDropdown = document.getElementById("profileDropdown");

  if (profileIcon && profileDropdown) {
    profileIcon.addEventListener("click", e => {
      e.stopPropagation();
      profileDropdown.classList.toggle("show");
    });
    document.addEventListener("click", e => {
      if (!profileIcon.contains(e.target) && !profileDropdown.contains(e.target)) {
        profileDropdown.classList.remove("show");
      }
    });
  }

  /* ── UPDATE PROFILE INFO ── */
  function updateProfileInfo() {
    const patient = JSON.parse(localStorage.getItem("patient") || "{}");
    const name    = localStorage.getItem("name") || patient.name || "";

    const profileIconEl  = document.getElementById("profileIcon");
    const dropdownAvatar = document.getElementById("dropdownAvatar");
    const dropdownName   = document.getElementById("dropdownName");
    const dropdownEmail  = document.getElementById("dropdownEmail");

    if (name) {
      const initial = name.charAt(0).toUpperCase();
      const gender  = (patient.gender || "").toLowerCase();
      let avatar = "👤";
      let gradient = "linear-gradient(135deg, #4FC3F7, #7C4DFF)";
      
      if (gender === "female") {
        avatar = "👩";
        gradient = "linear-gradient(135deg, #FF8E8E, #FF6B6B)";
      } else if (gender === "male") {
        avatar = "👨";
        gradient = "linear-gradient(135deg, #4A90E2, #6BA5F0)";
      } else {
        avatar = initial;
      }

      if (profileIconEl) {
        profileIconEl.textContent = avatar;
        profileIconEl.style.background = gradient;
      }
      if (dropdownAvatar) {
        dropdownAvatar.textContent = avatar;
        dropdownAvatar.style.background = gradient;
      }
      if (dropdownName)   dropdownName.textContent = name;
      if (dropdownEmail)  dropdownEmail.textContent = localStorage.getItem("phone") || "No phone number";
    } else {
      if (dropdownName)  dropdownName.textContent = "Guest User";
      if (dropdownEmail) dropdownEmail.textContent = "Not signed in";
    }
  }

  updateProfileInfo();

  /* ── APPLY SAVED THEME ON LOAD ── */
  const savedTheme = localStorage.getItem("theme");
  if (savedTheme === "light") {
    document.body.classList.add("light-theme");
    const btn = document.getElementById("themeToggleBtn");
    if (btn) btn.textContent = "🌙";
  } else {
    document.body.classList.add("dark-theme");
    const btn = document.getElementById("themeToggleBtn");
    if (btn) btn.textContent = "☀️";
  }

  // Welcome message on load
  setTimeout(() => {
    addCaptionToHistory(t('welcome'), 'ai');
  }, 500);

}); // end DOMContentLoaded


/* ── GLOBAL FUNCTIONS ── */

function toggleTheme() {
  const isLight = document.body.classList.toggle("light-theme");
  localStorage.setItem("theme", isLight ? "light" : "dark");
  const btn = document.getElementById("themeToggleBtn");
  if (btn) btn.textContent = isLight ? "🌙" : "☀️";
}

function logout() {
  if (confirm("Are you sure you want to logout?")) {
    localStorage.clear();
    window.location.href = "login.html";
  }
}

/* ── LOADER ── */
function showLoader() {
  const loader = document.getElementById("loaderOverlay");
  if (loader) loader.classList.add("show");
}
function hideLoader() {
  const loader = document.getElementById("loaderOverlay");
  if (loader) loader.classList.remove("show");
}

/* ── SUCCESS POPUP ── */
function showSuccessPopup(msg) {
  const successMsg = document.getElementById("successMsg");
  if (successMsg && msg) successMsg.textContent = msg;
  const popup = document.getElementById("successPopup");
  if (popup) popup.classList.add("show");
  
  // Auto-hide after 3 seconds
  setTimeout(() => {
    closeSuccessPopup();
  }, 3000);
}
function closeSuccessPopup() {
  const popup = document.getElementById("successPopup");
  if (popup) popup.classList.remove("show");
}

/* ── CALENDAR POPUP ── */
let calPopupDate    = new Date();
let calPopupResolve = null;

function openCalendarPopup() {
  return new Promise(resolve => {
    calPopupResolve = resolve;
    calPopupDate = new Date();
    renderCalPopup();
    const popup = document.getElementById("calendarPopup");
    if (popup) popup.classList.add("show");
  });
}

function closeCalendarPopup() {
  const popup = document.getElementById("calendarPopup");
  if (popup) popup.classList.remove("show");
}

function calChangeMonth(dir) {
  calPopupDate.setMonth(calPopupDate.getMonth() + dir);
  renderCalPopup();
}

function renderCalPopup() {
  const year  = calPopupDate.getFullYear();
  const month = calPopupDate.getMonth();
  const today = new Date(); 
  today.setHours(0,0,0,0);

  const labelEl = document.getElementById("calPopupLabel");
  if (labelEl) {
    labelEl.textContent = calPopupDate.toLocaleDateString("en-IN", { month: "long", year: "numeric" });
  }

  const grid = document.getElementById("calPopupGrid");
  if (!grid) return;
  grid.innerHTML = "";

  ["Su","Mo","Tu","We","Th","Fr","Sa"].forEach(d => {
    const h = document.createElement("div");
    h.className = "ch"; 
    h.textContent = d; 
    grid.appendChild(h);
  });

  const firstDay    = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  for (let i = 0; i < firstDay; i++) {
    const blank = document.createElement("div");
    blank.style.height = "32px";
    grid.appendChild(blank);
  }

  for (let d = 1; d <= daysInMonth; d++) {
    const cell     = document.createElement("div");
    cell.className = "cd";
    cell.textContent = d;

    const thisDate = new Date(year, month, d);
    const dateStr  = `${year}-${String(month+1).padStart(2,"0")}-${String(d).padStart(2,"0")}`;

    if (thisDate.getTime() === today.getTime()) cell.classList.add("today");
    if (thisDate < today) cell.classList.add("past");

    cell.onclick = () => {
      closeCalendarPopup();
      if (calPopupResolve) calPopupResolve(dateStr);
      calPopupResolve = null;
    };

    grid.appendChild(cell);
  }
}

/* ── REGION POPUP ── */
let regionResolve = null;

function openRegionPopup() {
  return new Promise(resolve => {
    regionResolve = resolve;
    const selectEl = document.getElementById("regionSelect");
    if (selectEl) selectEl.value = "";
    const popup = document.getElementById("regionPopup");
    if (popup) popup.classList.add("show");
  });
}

function closeRegionPopup() {
  const popup = document.getElementById("regionPopup");
  if (popup) popup.classList.remove("show");
}
// ── ASK REGION ON FIRST LOAD ──
const savedRegion = localStorage.getItem("selected_region");
if (!savedRegion) {
  // Small delay so page loads first
  setTimeout(async () => {
    const region = await openRegionPopup();
    if (region) {
      localStorage.setItem("selected_region", region);
      addCaptionToHistory(t('regionSet', region), 'ai');
    }
  }, 800);
}
function confirmRegion() {
  const selectEl = document.getElementById("regionSelect");
  const val = selectEl ? selectEl.value : "";
  if (!val) { 
    alert("Please select a region."); 
    return; 
  }
  localStorage.setItem("selected_region", val); // ← ADD THIS
  closeRegionPopup();
  if (regionResolve) regionResolve(val);
  regionResolve = null;
}