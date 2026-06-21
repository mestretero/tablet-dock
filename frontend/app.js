// Tablet dock - panel mantığı. Vanilla JS, bağımlılık yok.
// Tablet ince istemci: sadece gösterir + dokunuşu PC ajanına iletir.

const $ = (sel) => document.querySelector(sel);

async function api(path, body) {
  const opt = body
    ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }
    : {};
  const res = await fetch("/api" + path, opt);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// --- Saat -------------------------------------------------------------------
const DAYS = ["Pazar", "Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi"];
const MONTHS = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
  "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"];

function tickClock() {
  const now = new Date();
  const hh = String(now.getHours()).padStart(2, "0");
  const mm = String(now.getMinutes()).padStart(2, "0");
  $("#clock").textContent = `${hh}:${mm}`;
  $("#date").textContent = `${DAYS[now.getDay()]}, ${now.getDate()} ${MONTHS[now.getMonth()]}`;
}

// --- Burn-in koruması: kapsayıcıyı periyodik birkaç px kaydır --------------
function pixelShift() {
  const x = (Math.random() * 6 - 3).toFixed(1);
  const y = (Math.random() * 6 - 3).toFixed(1);
  $(".shift").style.transform = `translate(${x}px, ${y}px)`;
}

// --- Başlatıcı --------------------------------------------------------------
let _appsSig = "";
async function loadApps() {
  const box = $("#apps");
  let apps;
  try { apps = await api("/apps"); }
  catch {                              // ajan kapalı -> mevcut listeyi koru
    if (!box.querySelector(".app-tile")) {
      box.innerHTML = '<div class="apps-empty">Ajana bağlanılamadı.</div>';
    }
    return;
  }
  const sig = apps.map((a) => a.id).join(",");
  if (sig === _appsSig && box.querySelector(".app-tile")) return;  // değişmediyse çizme
  _appsSig = sig;
  if (!apps.length) {
    box.innerHTML = '<div class="apps-empty">apps.json boş — program ekleyin.</div>';
    return;
  }
  box.innerHTML = "";
  for (const app of apps) {
    const tile = document.createElement("button");
    tile.className = "app-tile";
    tile.dataset.appId = app.id;

    let icon;
    if (app.img) {
      icon = document.createElement("img");
      icon.className = "app-img";
      icon.src = "/api/app-icon/" + app.id;
      icon.alt = "";
      icon.onerror = () => {              // ikon çıkarılamazsa harf monogramına düş
        const span = document.createElement("span");
        span.className = "app-icon";
        span.textContent = app.icon;
        icon.replaceWith(span);
      };
    } else {
      icon = document.createElement("span");
      icon.className = "app-icon";
      icon.textContent = app.icon;
    }
    const name = document.createElement("span");
    name.className = "app-name";
    name.textContent = app.name;

    tile.append(icon, name);
    tile.addEventListener("click", () => launchApp(app.id, tile));
    box.appendChild(tile);
  }
}

async function launchApp(id, tile) {
  tile.classList.add("launched");
  setTimeout(() => tile.classList.remove("launched"), 500);
  try { await api("/launch", { id }); } catch { /* sessiz */ }
  setTimeout(pollStats, 800);   // açıldı/kapandı -> yanan durumu güncelle
}

// --- Oyunlar (Steam + Epic, kapak resimleriyle) -----------------------------
let _gamesSig = "";
async function loadGames() {
  const box = $("#games");
  let list;
  try { list = await api("/games"); }
  catch { return; }   // ajan kapalı -> mevcut listeyi koru
  const sig = list.map((g) => g.id).join(",");
  if (sig === _gamesSig && box.querySelector(".game-card")) return;  // değişmediyse çizme
  _gamesSig = sig;
  if (!list.length) {
    box.innerHTML = '<div class="games-empty">Yüklü oyun bulunamadı.</div>';
    return;
  }
  box.innerHTML = "";
  for (const g of list) {
    const card = document.createElement("button");
    card.className = "game-card" + (g.has_cover ? "" : " no-cover") + (g.fit === "contain" ? " fit-contain" : "");
    if (g.has_cover) {
      const img = document.createElement("img");
      img.src = "/api/game-cover/" + g.id;
      img.alt = "";
      img.onerror = () => { img.remove(); card.classList.add("no-cover"); };
      card.appendChild(img);
    }
    const name = document.createElement("span");
    name.className = "game-name";
    name.textContent = g.name;
    card.appendChild(name);
    card.addEventListener("click", () => launchGame(g.id, card));
    box.appendChild(card);
  }
}

async function launchGame(id, card) {
  card.classList.add("launched");
  setTimeout(() => card.classList.remove("launched"), 600);
  try { await api("/game-launch", { id }); } catch { /* sessiz */ }
}

// --- Proje klasörleri (canlı, köke göre gruplu) -----------------------------
const FOLDER_SVG =
  '<svg viewBox="0 0 24 24"><path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg>';

async function loadProjects() {
  const box = $("#projects");
  let groups;
  try { groups = await api("/projects"); }
  catch { return; }   // ajan kapalı olabilir -> mevcut listeyi koru
  box.innerHTML = "";
  for (const g of groups) {
    const group = document.createElement("div");
    const label = document.createElement("div");
    label.className = "proj-group-label";
    label.textContent = g.root_name;
    group.appendChild(label);

    const chips = document.createElement("div");
    chips.className = "proj-chips";
    if (!g.folders.length) {
      const empty = document.createElement("div");
      empty.className = "proj-empty";
      empty.textContent = "Henüz klasör yok";
      chips.appendChild(empty);
    } else {
      for (const f of g.folders) {
        const chip = document.createElement("button");
        chip.className = "proj-chip";
        chip.innerHTML = FOLDER_SVG + '<span class="pc-name"></span>';
        chip.querySelector(".pc-name").textContent = f.name;   // textContent = XSS yok
        chip.title = f.name;
        chip.addEventListener("click", () => openProject(f.path, chip));
        chips.appendChild(chip);
      }
    }
    group.appendChild(chips);
    box.appendChild(group);
  }
}

async function openProject(path, chip) {
  chip.classList.add("opened");
  setTimeout(() => chip.classList.remove("opened"), 500);
  try { await api("/open-folder", { path }); } catch { /* sessiz */ }
}

// Projeler bölümünü aç/kapa (tercih hatırlanır, varsayılan kapalı)
const projToggle = $("#projToggle");
const projBox = $("#projects");
function setProjOpen(open) {
  projBox.hidden = !open;
  projToggle.setAttribute("aria-expanded", open ? "true" : "false");
  try { localStorage.setItem("projOpen", open ? "1" : "0"); } catch { /* yok say */ }
}
projToggle.addEventListener("click", () => setProjOpen(projBox.hidden));
setProjOpen((() => {
  try { return localStorage.getItem("projOpen") === "1"; } catch { return false; }
})());

// --- Medya + ses ------------------------------------------------------------
document.querySelectorAll("[data-media]").forEach((btn) =>
  btn.addEventListener("click", async () => {
    await api("/media", { action: btn.dataset.media }).catch(() => {});
    setTimeout(pollStats, 400);   // çalma durumu ikonu hızlı güncellensin
  })
);

// Oynat/duraklat butonunun ikonunu çalma durumuna göre çevir.
function setPlayPauseIcon(playing) {
  const svg = document.querySelector("#ppBtn svg");
  if (!svg) return;
  svg.innerHTML = playing
    ? '<path d="M8 5v14M16 5v14"/>'                              // çalıyor -> duraklat (||)
    : '<path d="M8 6v12l10-6z" fill="#1a1206" stroke="none"/>';  // duraklı -> oynat (▶)
}

const vol = $("#vol");
const volVal = $("#volVal");
let volTimer = null;

vol.addEventListener("input", () => {
  volVal.textContent = vol.value;
  // Sürüklerken ajanı boğmamak için son değeri kısa gecikmeyle gönder.
  clearTimeout(volTimer);
  volTimer = setTimeout(() => api("/volume", { level: Number(vol.value) }).catch(() => {}), 120);
});

let muted = false;
$("#muteBtn").addEventListener("click", async () => {
  muted = !muted;
  $("#muteBtn").classList.toggle("muted", muted);
  try { await api("/volume", { muted }); } catch { /* sessiz */ }
});

async function syncVolume() {
  try {
    const v = await api("/volume", {});        // boş gövde = mevcut durumu döndürür (POST)
    vol.value = v.level;
    volVal.textContent = v.level;
    muted = v.muted;
    $("#muteBtn").classList.toggle("muted", muted);
  } catch { /* ajan kapalı olabilir */ }
}

// --- Ses çıkışı seçici (2 cihaz hızlı geçiş) --------------------------------
async function loadAudio() {
  const box = $("#audioOut");
  let outs;
  try { outs = await api("/audio"); } catch { return; }
  box.innerHTML = "";
  for (const o of outs) {
    const b = document.createElement("button");
    b.className = "ao-btn" + (o.active ? " active" : "");
    b.textContent = o.label;
    if (!o.available) b.disabled = true;
    else b.addEventListener("click", () => setAudio(o.key));
    box.appendChild(b);
  }
}

async function setAudio(key) {
  try { await api("/audio", { key }); } catch { /* sessiz */ }
  loadAudio();   // aktif vurguyu hemen güncelle
}

// --- Uygulama-bazlı ses mikseri ---------------------------------------------
let mixerActiveKey = null;   // şu an sürüklenen kaydırağın anahtarı (clobber'ı önler)

async function loadMixer() {
  let data;
  try { data = await api("/mixer"); } catch { return; }
  renderMixer(data.sessions);
}

function renderMixer(sessions) {
  const box = $("#mixer");
  const seen = new Set();
  for (const s of sessions) {
    seen.add(s.key);
    let row = box.querySelector(`.mx-row[data-key="${CSS.escape(s.key)}"]`);
    if (!row) row = createMixerRow(s, box);
    row.querySelector(".mx-label").textContent = s.label;
    row.querySelector(".mx-mute").classList.toggle("muted", s.muted);
    if (mixerActiveKey !== s.key) {        // sürüklenen satırı ezme
      row.querySelector(".mx-slider").value = s.level;
      row.querySelector(".mx-val").textContent = s.level;
    }
  }
  box.querySelectorAll(".mx-row").forEach((r) => {   // kapanan uygulamaları kaldır
    if (!seen.has(r.dataset.key)) r.remove();
  });
  if (!box.querySelector(".mx-row")) {
    box.innerHTML = '<div class="mx-empty">Ses çalan uygulama yok.</div>';
  }
}

function createMixerRow(s, box) {
  const empty = box.querySelector(".mx-empty");
  if (empty) empty.remove();
  const row = document.createElement("div");
  row.className = "mx-row";
  row.dataset.key = s.key;
  row.innerHTML =
    '<button class="mx-mute mbtn mbtn-sm" aria-label="Sustur">' +
    '<svg viewBox="0 0 24 24"><path d="M4 9v6h4l5 4V5L8 9H4z"/></svg></button>' +
    '<div class="mx-info"><span class="mx-label"></span>' +
    `<input class="mx-slider slider" type="range" min="0" max="100" value="${s.level}"></div>` +
    `<span class="mx-val">${s.level}</span>`;

  const slider = row.querySelector(".mx-slider");
  let t = null;
  slider.addEventListener("input", () => {
    mixerActiveKey = s.key;
    row.querySelector(".mx-val").textContent = slider.value;
    clearTimeout(t);
    t = setTimeout(() => api("/mixer", { key: s.key, level: Number(slider.value) }).catch(() => {}), 120);
  });
  // sürükleme bitince kısa süre sonra poll güncellemesine izin ver
  slider.addEventListener("change", () => setTimeout(() => { mixerActiveKey = null; }, 500));

  const mute = row.querySelector(".mx-mute");
  mute.addEventListener("click", () => {
    const nowMuted = !mute.classList.contains("muted");
    mute.classList.toggle("muted", nowMuted);
    api("/mixer", { key: s.key, muted: nowMuted }).catch(() => {});
  });

  box.appendChild(row);
  return row;
}

// --- Pano geçmişi -----------------------------------------------------------
async function loadClipboard() {
  const box = $("#clipboard");
  let items;
  try { items = await api("/clipboard"); } catch { return; }
  box.innerHTML = "";
  if (!items.length) {
    box.innerHTML = '<div class="clip-empty">Pano boş — bir şey kopyala.</div>';
    return;
  }
  for (const it of items) {
    const b = document.createElement("button");
    b.className = "clip-item";
    b.textContent = it.preview;
    b.title = it.preview;
    b.addEventListener("click", () => copyClip(it.index, b));
    box.appendChild(b);
  }
}

async function copyClip(index, btn) {
  try { await api("/clipboard", { index }); } catch { return; }
  btn.classList.add("copied");
  btn.textContent = "Panoya kopyalandı";
  setTimeout(loadClipboard, 900);   // kullanılanı başa taşır + butonu tazeler
}

// --- PC durumu (poll) -------------------------------------------------------
async function pollStats() {
  try {
    const s = await api("/stats");
    $("#cpu").textContent = s.cpu;
    $("#ram").textContent = s.ram;
    $("#cpuBar").style.width = s.cpu + "%";
    $("#ramBar").style.width = s.ram + "%";

    const np = $("#np");
    if (s.now_playing) {
      $("#npTitle").textContent = s.now_playing.title;
      $("#npArtist").textContent = s.now_playing.artist || "";
      np.hidden = false;
    } else {
      np.hidden = true;
    }
    setPlayPauseIcon(s.now_playing && s.now_playing.playing);

    // Açık programların tile'ını yak
    const running = new Set(s.running_apps || []);
    document.querySelectorAll(".app-tile").forEach((t) => {
      t.classList.toggle("running", running.has(t.dataset.appId));
    });
  } catch { /* ajan kapalı - panel yine ayakta */ }
}

// --- Asistan: cevap gösterimi + sesli okuma ---------------------------------
function setReply(text, thinking) {
  const reply = $("#chatReply");
  reply.hidden = false;
  reply.classList.toggle("thinking", !!thinking);
  reply.textContent = text;
}

function speak(text) {
  if (!text) return;
  // Fully Kiosk'un native TTS'i varsa onu kullan (daha iyi Android sesi).
  if (window.fully && typeof fully.textToSpeech === "function") {
    fully.textToSpeech(text);
    return;
  }
  if (window.speechSynthesis) {
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "tr-TR";
    speechSynthesis.cancel();
    speechSynthesis.speak(u);
  }
}

function stopSpeaking() {
  if (window.fully && typeof fully.stopTextToSpeech === "function") fully.stopTextToSpeech();
  if (window.speechSynthesis) speechSynthesis.cancel();
}

// --- Sesli asistan: iki buton (Sor=Gemma yerel, İnternette ara=Claude) ------
const micBtn = $("#micBtn");
const micWebBtn = $("#micWebBtn");
const micHint = $("#micHint");
let micState = "idle";        // idle | rec | busy
let recordMode = "local";     // local | web
let mediaRecorder = null;
let chunks = [];
let micStream = null;

function render() {
  for (const b of [micBtn, micWebBtn]) b.classList.remove("recording", "thinking");
  if (micState === "idle") { micHint.textContent = "Konuşmak için dokun"; return; }
  (recordMode === "web" ? micWebBtn : micBtn).classList.add(micState === "rec" ? "recording" : "thinking");
  micHint.textContent = micState === "rec"
    ? (recordMode === "web" ? "İnternette dinliyorum… dokun bitir" : "Dinliyorum… dokun bitir")
    : "Düşünüyor…";
}

async function startRec(mode) {
  stopSpeaking();                        // barge-in: konuşuyorsa sustur
  recordMode = mode;
  micState = "rec";
  render();                              // ANINDA görsel tepki (mikrofon gelmeden)
  try {
    micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch {
    micState = "idle"; render();
    setReply("Mikrofon erişilemedi.", false);
    return;
  }
  if (micState !== "rec") {              // bu arada durdurulduysa iptal
    micStream.getTracks().forEach((t) => t.stop()); micStream = null;
    return;
  }
  chunks = [];
  mediaRecorder = new MediaRecorder(micStream);
  mediaRecorder.ondataavailable = (e) => { if (e.data.size) chunks.push(e.data); };
  mediaRecorder.onstop = sendAudio;
  mediaRecorder.start();
}

function stopRec() {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    micState = "busy"; render();
    mediaRecorder.stop();                // -> onstop -> sendAudio
  } else {
    if (micStream) { micStream.getTracks().forEach((t) => t.stop()); micStream = null; }
    micState = "idle"; render();
  }
}

async function sendAudio() {
  const blob = new Blob(chunks, { type: mediaRecorder.mimeType || "audio/webm" });
  if (micStream) { micStream.getTracks().forEach((t) => t.stop()); micStream = null; }
  if (!blob.size) { micState = "idle"; render(); return; }
  const url = recordMode === "web" ? "/api/voice?web=true" : "/api/voice";
  setReply("Düşünüyor…", true);
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/octet-stream" },
      body: blob,
    });
    const r = await res.json();
    const heard = r.transcript ? `“${r.transcript}”\n\n` : "";
    setReply(heard + r.reply, false);
    speak(r.reply);
  } catch {
    setReply("Cevap alınamadı.", false);
  }
  micState = "idle"; render();
}

// Dokun = başlat (o modda), tekrar dokun = bitir + gönder. Meşgulken yok say.
function onMicTap(mode) {
  if (micState === "idle") startRec(mode);
  else if (micState === "rec") stopRec();
}
micBtn.addEventListener("click", () => onMicTap("local"));
micWebBtn.addEventListener("click", () => onMicTap("web"));

// --- Sekme geçişi (alt pill nav) --------------------------------------------
const _tabs = document.querySelectorAll(".tab");
const _tabBtns = document.querySelectorAll(".tab-btn");
function showTab(name) {
  _tabs.forEach((t) => { t.hidden = t.dataset.tab !== name; });
  _tabBtns.forEach((b) => b.classList.toggle("active", b.dataset.go === name));
  try { localStorage.setItem("activeTab", name); } catch { /* yok say */ }
  if (name === "medya") { loadMixer(); loadAudio(); }   // anında tazele
  window.scrollTo(0, 0);
}
_tabBtns.forEach((b) => b.addEventListener("click", () => showTab(b.dataset.go)));
showTab((() => {
  try { return localStorage.getItem("activeTab") || "ana"; } catch { return "ana"; }
})());

// --- Kiosk davranışı (Chrome PWA) -------------------------------------------
// Service worker: Chrome'un "Uygulamayı yükle" (tam ekran) demesi için.
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js").catch(() => {});
}

// Ekranı açık tut (duvar paneli uyumasın).
let wakeLock = null;
async function keepAwake() {
  try {
    if ("wakeLock" in navigator) wakeLock = await navigator.wakeLock.request("screen");
  } catch { /* izin yok / desteklenmiyor */ }
}
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible") keepAwake();
});
keepAwake();

// Tarayıcı sekmesinde açıldıysa ilk dokunuşta tam ekrana geç (PWA'da zaten tam ekran).
document.addEventListener("click", () => {
  if (!document.fullscreenElement && document.documentElement.requestFullscreen) {
    document.documentElement.requestFullscreen().catch(() => {});
  }
}, { once: true });

// --- Başlat -----------------------------------------------------------------
tickClock();
setInterval(tickClock, 1000);
setInterval(pixelShift, 60000);   // dakikada bir burn-in kaydırma

loadApps();
setInterval(loadApps, 15000);       // eklenen/silinen programları otomatik yansıt
loadGames();
setInterval(loadGames, 30000);      // yüklenen/silinen oyunları otomatik yansıt
loadProjects();
setInterval(loadProjects, 20000);   // yeni/silinen proje klasörlerini otomatik yansıt
syncVolume();
loadAudio();
setInterval(loadAudio, 8000);       // ses çıkışı durumu senkron kalsın
loadMixer();
setInterval(loadMixer, 4000);       // açılan/kapanan uygulama seslerini yansıt
loadClipboard();
setInterval(loadClipboard, 4000);   // pano geçmişi senkron kalsın
pollStats();
setInterval(pollStats, 3000);
