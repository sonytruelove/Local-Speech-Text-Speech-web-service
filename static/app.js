const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const statusEl = document.getElementById("status");
const transcriptEl = document.getElementById("transcript");
const player = document.getElementById("player");

let mediaRecorder = null;
let chunks = [];

function setStatus(text) {
  statusEl.textContent = text;
}

startBtn.addEventListener("click", async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    chunks = [];
    mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" });
    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunks.push(e.data);
    };
    mediaRecorder.onstop = onRecordingStop;
    mediaRecorder.start();

    startBtn.disabled = true;
    stopBtn.disabled = false;
    transcriptEl.textContent = "";
    player.removeAttribute("src");
    setStatus("Идёт запись...");
  } catch (err) {
    setStatus("Не удалось получить доступ к микрофону: " + err.message);
  }
});

stopBtn.addEventListener("click", () => {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
    mediaRecorder.stream.getTracks().forEach((t) => t.stop());
  }
  startBtn.disabled = false;
  stopBtn.disabled = true;
});

async function onRecordingStop() {
  const blob = new Blob(chunks, { type: "audio/webm" });
  setStatus("Распознаём речь...");

  try {
    const form = new FormData();
    form.append("file", blob, "speech.webm");

    const transcribeRes = await fetch("/api/transcribe", { method: "POST", body: form });
    if (!transcribeRes.ok) throw new Error(await transcribeRes.text());
    const { text, language } = await transcribeRes.json();

    transcriptEl.textContent = text || "(пусто)";
    if (!text) {
      setStatus("Речь не распознана — попробуйте ещё раз");
      return;
    }

    setStatus(`Озвучиваем (язык: ${language})...`);
    const synthRes = await fetch("/api/synthesize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!synthRes.ok) throw new Error(await synthRes.text());

    const audioBlob = await synthRes.blob();
    player.src = URL.createObjectURL(audioBlob);
    await player.play();
    setStatus("Готово");
  } catch (err) {
    setStatus("Ошибка: " + err.message);
  }
}
