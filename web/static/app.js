const thread = document.getElementById("thread");
const form = document.getElementById("ask-form");
const input = document.getElementById("question");
const send = document.getElementById("send");
const fileInput = document.getElementById("file");
const resumeLabel = document.getElementById("resume-label");
const resumeMeta = document.getElementById("resume-meta");
const uploadStatus = document.getElementById("upload-status");
const suggestions = document.getElementById("suggestions");
const newChatBtn = document.getElementById("new-chat");

function esc(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function showEmpty() {
  thread.innerHTML = `<div class="empty">Upload a resume, then ask me about my experience, skills, projects — or generate interview questions.</div>`;
  suggestions.hidden = false;
}

showEmpty();

async function refreshResumeStatus() {
  try {
    const data = await fetch("/api/resume").then((r) => r.json());
    if (data.uploaded) {
      resumeLabel.textContent = data.filename || "Resume ready";
      resumeMeta.textContent = `Studied · ${data.chars.toLocaleString()} characters`;
    } else {
      resumeLabel.textContent = "No resume uploaded yet";
      resumeMeta.textContent = "PDF, DOCX, TXT, or MD · max 8MB";
    }
  } catch (_) {
    /* ignore */
  }
}

refreshResumeStatus();

suggestions.querySelectorAll("button").forEach((btn) => {
  btn.addEventListener("click", () => {
    input.value = btn.dataset.q;
    form.requestSubmit();
  });
});

newChatBtn.addEventListener("click", () => {
  showEmpty();
  input.focus();
});

fileInput.addEventListener("change", async () => {
  const file = fileInput.files && fileInput.files[0];
  if (!file) return;
  uploadStatus.hidden = false;
  uploadStatus.textContent = "Studying resume…";
  const body = new FormData();
  body.append("file", file);
  try {
    const res = await fetch("/api/upload", { method: "POST", body });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Upload failed");
    uploadStatus.textContent = data.message || "Resume ready.";
    await refreshResumeStatus();
    appendAssistant({
      answer: `I've studied "${data.filename}". I'm ready — ask me anything about my background, or ask for interview questions.`,
      can_answer: true,
      kind: "greeting",
      sources: [],
    });
  } catch (err) {
    uploadStatus.textContent = err.message || "Upload failed";
  } finally {
    fileInput.value = "";
  }
});

function appendUser(question) {
  if (thread.querySelector(".empty")) thread.innerHTML = "";
  suggestions.hidden = true;
  const el = document.createElement("article");
  el.className = "msg user";
  el.innerHTML = `<div class="label">You</div><div class="answer">${esc(question)}</div>`;
  thread.appendChild(el);
  el.scrollIntoView({ behavior: "smooth", block: "end" });
}

function appendAssistant(data) {
  if (thread.querySelector(".empty")) thread.innerHTML = "";
  const el = document.createElement("article");
  el.className = "msg assistant";

  const sources = (data.sources || []).slice(0, 3);
  const sourcesHtml =
    data.kind === "answer" && sources.length
      ? `<div class="sources"><div class="title">Background</div>${sources
          .map(
            (s) =>
              `<div class="source"><strong>${esc(s.label || "Resume")}</strong>${
                s.section ? ` · ${esc(s.section)}` : ""
              }<div>${esc((s.excerpt || "").slice(0, 180))}${(s.excerpt || "").length > 180 ? "…" : ""}</div></div>`
          )
          .join("")}</div>`
      : "";

  el.innerHTML = `<div class="label">Candidate</div><div class="answer">${esc(data.answer)}</div>${sourcesHtml}`;
  thread.appendChild(el);
  el.scrollIntoView({ behavior: "smooth", block: "end" });
}

function showTyping() {
  const el = document.createElement("article");
  el.className = "msg assistant";
  el.id = "typing";
  el.innerHTML = `<div class="label">Candidate</div><div class="typing"><i></i><i></i><i></i></div>`;
  thread.appendChild(el);
  el.scrollIntoView({ behavior: "smooth", block: "end" });
}

function hideTyping() {
  const el = document.getElementById("typing");
  if (el) el.remove();
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = input.value.trim();
  if (!question) return;
  appendUser(question);
  input.value = "";
  send.disabled = true;
  send.textContent = "…";
  showTyping();
  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const data = await res.json();
    hideTyping();
    if (!res.ok) {
      appendAssistant({
        answer: typeof data.detail === "string" ? data.detail : "Ask me something about my background.",
        can_answer: false,
        kind: "off_topic",
        sources: [],
      });
    } else {
      appendAssistant(data);
    }
  } catch (_) {
    hideTyping();
    appendAssistant({
      answer: "Ask me something about my background.",
      can_answer: false,
      kind: "off_topic",
      sources: [],
    });
  } finally {
    send.disabled = false;
    send.textContent = "Ask";
    input.focus();
  }
});

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});
