// Domain AI - Client Application Logic
// Dynamic data loading - zero hardcoding

const state = {
  models: [],
  selectedModelId: "",
  isGenerating: false,
  messages: []
};

// DOM Elements
const modelSelect = document.getElementById("modelSelect");
const modelStatusText = document.getElementById("modelStatusText");
const queryList = document.getElementById("queryList");
const messagesContainer = document.getElementById("messagesContainer");
const welcomeCard = document.getElementById("welcomeCard");
const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const clearChatBtn = document.getElementById("clearChatBtn");
const activeModelTitle = document.getElementById("activeModelTitle");
const activeModelSub = document.getElementById("activeModelSub");

// Initialize application
async function init() {
  await Promise.all([loadModels(), loadQuickQueries()]);
  setupEventListeners();
}

// 1. Fetch models dynamically from backend
async function loadModels() {
  try {
    const res = await fetch("/api/models");
    const data = await res.json();
    state.models = data.models || [];

    modelSelect.innerHTML = "";

    if (state.models.length === 0) {
      modelSelect.innerHTML = '<option value="">No models found</option>';
      modelStatusText.textContent = "No models available";
      return;
    }

    state.models.forEach((m, idx) => {
      const opt = document.createElement("option");
      opt.value = m.model_id;
      const baseName = m.base_model_id ? m.base_model_id.split("/").pop() : "Custom";
      opt.textContent = `${baseName} (${m.deployment_status || "READY"})`;
      modelSelect.appendChild(opt);
    });

    modelSelect.disabled = false;
    state.selectedModelId = state.models[0].model_id;
    updateActiveModelDisplay();
    sendBtn.disabled = false;
    modelStatusText.textContent = `${state.models.length} model(s) connected`;
  } catch (err) {
    console.error("Failed to load models:", err);
    modelStatusText.textContent = "Failed to load models";
  }
}

// 2. Fetch sample queries dynamically
async function loadQuickQueries() {
  try {
    const res = await fetch("/api/queries");
    const data = await res.json();
    const queries = data.queries || [];

    queryList.innerHTML = "";
    queries.forEach((q) => {
      const btn = document.createElement("button");
      btn.className = "query-btn";
      btn.textContent = q;
      btn.addEventListener("click", () => {
        messageInput.value = q;
        messageInput.focus();
      });
      queryList.appendChild(btn);
    });
  } catch (err) {
    console.error("Failed to load queries:", err);
    queryList.innerHTML = '<p class="text-muted">No quick queries available</p>';
  }
}

function updateActiveModelDisplay() {
  const m = state.models.find((item) => item.model_id === state.selectedModelId);
  if (m) {
    activeModelTitle.textContent = m.base_model_id || "Domain Aligned Model";
    activeModelSub.textContent = `ID: ${m.model_id} • Status: ${m.deployment_status || "DEPLOYED"}`;
  }
}

function setupEventListeners() {
  modelSelect.addEventListener("change", (e) => {
    state.selectedModelId = e.target.value;
    updateActiveModelDisplay();
  });

  messageInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!state.isGenerating && messageInput.value.trim()) {
        handleSubmit();
      }
    }
  });

  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    if (!state.isGenerating && messageInput.value.trim()) {
      handleSubmit();
    }
  });

  clearChatBtn.addEventListener("click", () => {
    state.messages = [];
    messagesContainer.innerHTML = "";
    if (welcomeCard) messagesContainer.appendChild(welcomeCard);
  });
}

async function handleSubmit() {
  const text = messageInput.value.trim();
  if (!text || !state.selectedModelId) return;

  if (welcomeCard && welcomeCard.parentNode) {
    welcomeCard.parentNode.removeChild(welcomeCard);
  }

  // 1. Add user message
  state.messages.push({ role: "user", content: text });
  appendMessage("user", text);
  messageInput.value = "";
  messageInput.style.height = "auto";

  // 2. Add loading assistant placeholder
  const loadingEl = appendMessage("assistant", "Thinking...");
  state.isGenerating = true;
  sendBtn.disabled = true;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model_id: state.selectedModelId,
        messages: state.messages,
        max_tokens: 450,
        temperature: 0.7
      })
    });

    const data = await res.json();
    if (res.ok && data.response) {
      state.messages.push({ role: "assistant", content: data.response });
      const bubble = loadingEl.querySelector(".message-bubble");
      bubble.textContent = data.response;

      const meta = document.createElement("div");
      meta.className = "message-meta";
      const totalTok = (data.usage?.prompt_tokens || 0) + (data.usage?.completion_tokens || 0);
      meta.textContent = `${totalTok} tokens • ${data.latency_seconds || 0}s latency`;
      loadingEl.appendChild(meta);
    } else {
      const bubble = loadingEl.querySelector(".message-bubble");
      bubble.textContent = `Error: ${data.error || "Failed to generate response"}`;
    }
  } catch (err) {
    const bubble = loadingEl.querySelector(".message-bubble");
    bubble.textContent = `Network Error: ${err.message}`;
  } finally {
    state.isGenerating = false;
    sendBtn.disabled = false;
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }
}

function appendMessage(role, text) {
  const row = document.createElement("div");
  row.className = `message-row ${role}`;

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";
  bubble.textContent = text;
  row.appendChild(bubble);

  messagesContainer.appendChild(row);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
  return row;
}

// Start app on page load
document.addEventListener("DOMContentLoaded", init);

