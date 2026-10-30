const state = {
  activeAgent: "support",
  isGenerating: false,
  messages: {
    support: [],
    research: []
  },
  sessionId: "session_" + Math.random().toString(36).substring(2, 9)
};

const agentMetadata = {
  support: {
    title: "Customer Support Agent",
    sub: "Fine-tuned Model: model_01m61gc299z19jd4 (ShopEase)",
    icon: "🎧",
    desc: "Powered by a LangChain LangGraph agent with checkpoint memory, directly fine-tuned on ShopEase marketplace procedures, counterfeit escalation hierarchy, warranties, and SLAs.",
    placeholder: "Ask about returns, warranties, damaged goods, or seller fulfillment rules..."
  },
  research: {
    title: "Research Paper Agent",
    sub: "Fine-tuned Model: model_01m61pt5v52a9jee (200 AI Papers)",
    icon: "🔬",
    desc: "Powered by a LangChain LangGraph agent with checkpoint memory, directly fine-tuned on 200 landmark AI research papers, attention mechanisms, PEFT, and LoRA formulations.",
    placeholder: "Ask about LoRA low-rank adaptation, scaled dot-product attention, or QLoRA quantization..."
  }
};

const btnSupportAgent = document.getElementById("btnSupportAgent");
const btnResearchAgent = document.getElementById("btnResearchAgent");
const activeAgentTitle = document.getElementById("activeAgentTitle");
const activeAgentSub = document.getElementById("activeAgentSub");
const welcomeCard = document.getElementById("welcomeCard");
const welcomeIcon = document.getElementById("welcomeIcon");
const welcomeTitle = document.getElementById("welcomeTitle");
const welcomeDesc = document.getElementById("welcomeDesc");
const queryList = document.getElementById("queryList");
const messagesContainer = document.getElementById("messagesContainer");
const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const clearChatBtn = document.getElementById("clearChatBtn");

async function init() {
  setupEventListeners();
  await loadQuickQueries("support");
}

function selectAgent(agentId) {
  if (state.activeAgent === agentId) return;
  state.activeAgent = agentId;

  if (agentId === "support") {
    btnSupportAgent.classList.add("active");
    btnResearchAgent.classList.remove("active");
  } else {
    btnResearchAgent.classList.add("active");
    btnSupportAgent.classList.remove("active");
  }

  const meta = agentMetadata[agentId];
  activeAgentTitle.textContent = meta.title;
  activeAgentSub.textContent = meta.sub;
  welcomeIcon.textContent = meta.icon;
  welcomeTitle.textContent = meta.title;
  welcomeDesc.textContent = meta.desc;
  messageInput.placeholder = meta.placeholder;

  renderActiveChat();
  loadQuickQueries(agentId);
}

function renderActiveChat() {
  messagesContainer.innerHTML = "";
  const currentMsgs = state.messages[state.activeAgent];
  if (currentMsgs.length === 0) {
    messagesContainer.appendChild(welcomeCard);
  } else {
    currentMsgs.forEach((m) => appendMessageUI(m.role, m.content, m.meta));
  }
}

async function loadQuickQueries(agentId) {
  try {
    const res = await fetch(`/api/queries?agent_type=${agentId}`);
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
  } catch (e) {
    queryList.innerHTML = '<p class="query-skeleton">No queries available</p>';
  }
}

function setupEventListeners() {
  btnSupportAgent.addEventListener("click", () => selectAgent("support"));
  btnResearchAgent.addEventListener("click", () => selectAgent("research"));

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
    state.messages[state.activeAgent] = [];
    renderActiveChat();
  });
}

async function handleSubmit() {
  const text = messageInput.value.trim();
  if (!text || state.isGenerating) return;

  if (welcomeCard && welcomeCard.parentNode) {
    welcomeCard.parentNode.removeChild(welcomeCard);
  }

  const agent = state.activeAgent;
  state.messages[agent].push({ role: "user", content: text });
  appendMessageUI("user", text);

  messageInput.value = "";
  messageInput.style.height = "auto";

  const loadingRow = appendMessageUI("assistant", "Agent reasoning via LangGraph...");
  state.isGenerating = true;
  sendBtn.disabled = true;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        agent_type: agent,
        messages: state.messages[agent],
        session_id: state.sessionId,
        max_tokens: 450,
        temperature: 0.3
      })
    });

    const data = await res.json();
    const reply = data.response || "No response generated";
    const bubble = loadingRow.querySelector(".message-bubble");
    bubble.textContent = reply;

    const meta = document.createElement("div");
    meta.className = "message-meta";
    meta.textContent = `${data.latency_seconds || 0}s latency • Checkpoint Thread: ${data.thread_id || "active"}`;
    loadingRow.appendChild(meta);

    state.messages[agent].push({
      role: "assistant",
      content: reply,
      meta: meta.textContent
    });
  } catch (err) {
    const bubble = loadingRow.querySelector(".message-bubble");
    bubble.textContent = `Error: ${err.message}`;
  } finally {
    state.isGenerating = false;
    sendBtn.disabled = false;
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }
}

function appendMessageUI(role, text, metaText) {
  const row = document.createElement("div");
  row.className = `message-row ${role}`;

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";
  bubble.textContent = text;
  row.appendChild(bubble);

  if (metaText) {
    const meta = document.createElement("div");
    meta.className = "message-meta";
    meta.textContent = metaText;
    row.appendChild(meta);
  }

  messagesContainer.appendChild(row);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
  return row;
}

document.addEventListener("DOMContentLoaded", init);
