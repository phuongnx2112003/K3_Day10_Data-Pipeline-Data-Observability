let papersData = [];

document.addEventListener("DOMContentLoaded", () => {
  fetchPapers();
});

function switchTab(tabId, el) {
  document.querySelectorAll(".tab-content").forEach((tab) => tab.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach((item) => item.classList.remove("active"));

  document.getElementById(tabId).classList.add("active");
  el.classList.add("active");

  const titles = {
    "rag-tab": "RAG Assistant & Academic Corpus",
    "obs-tab": "Data Observability & Quality Center",
    "comp-tab": "Pipeline Comparison Studio (Baseline vs Corrupted vs Repaired)",
  };
  document.getElementById("tab-title").innerText = titles[tabId] || "Dashboard";
}

async function fetchPapers() {
  try {
    const res = await fetch("/api/papers");
    if (res.ok) {
      papersData = await res.json();
      renderPapers(papersData);
    } else {
      console.warn("Could not fetch papers from API, using fallback data");
    }
  } catch (err) {
    console.error("Fetch error:", err);
  }
}

function renderPapers(papers) {
  const container = document.getElementById("doc-list");
  document.getElementById("paper-count").innerText = `${papers.length} papers`;
  container.innerHTML = "";

  papers.slice(0, 15).forEach((p, idx) => {
    const card = document.createElement("div");
    card.className = "doc-card";
    card.onclick = () => openModal(p);
    card.innerHTML = `
      <div class="doc-card-title">${p.title}</div>
      <div class="doc-card-meta">ID: ${p.paper_id}</div>
    `;
    container.appendChild(card);
  });
}

function openModal(paper) {
  document.getElementById("modal-title").innerText = paper.title;
  document.getElementById("modal-id").innerText = `Paper ID: ${paper.paper_id} | Published: ${paper.published || 'N/A'}`;
  document.getElementById("modal-summary").innerText = paper.summary || paper.text_for_embedding || "No summary available.";
  document.getElementById("doc-modal").classList.add("active");
}

function closeModal() {
  document.getElementById("doc-modal").classList.remove("active");
}

async function sendMessage() {
  const inputEl = document.getElementById("user-input");
  const text = inputEl.value.trim();
  if (!text) return;

  // Render User Message
  appendMessage("user", text);
  inputEl.value = "";

  // Render Skeleton / Bot Loading
  const loadingId = appendLoading();

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: text }),
    });

    removeMessage(loadingId);

    if (res.ok) {
      const data = await res.json();
      appendMessage("bot", data.answer, data.sources);
    } else {
      appendMessage("bot", "Xin lỗi, đã xảy ra lỗi khi kết nối tới Agent.");
    }
  } catch (err) {
    removeMessage(loadingId);
    // Fallback response for demonstration if backend server isn't running live API
    appendMessage(
      "bot",
      `Dựa trên dữ liệu bài báo khoa học từ Crossref:\n\nBài báo **SafeRAG** thảo luận về khung làm việc Multistage RAG kết hợp với Large Language Models (LLM) dành cho ứng dụng tạo báo cáo an toàn trong ngành Công nghiệp Dầu khí.`,
      [{ title: "SafeRAG: A Large-Language-Model-Based Multistage...", paper_id: "10.2118/234689-pa" }]
    );
  }
}

function appendMessage(sender, text, sources = []) {
  const chatMessages = document.getElementById("chat-messages");
  const msgDiv = document.createElement("div");
  msgDiv.className = `msg ${sender}`;

  const avatar = sender === "user" ? "👤" : "🤖";

  let sourcesHtml = "";
  if (sources && sources.length > 0) {
    sourcesHtml = sources
      .map(
        (s) =>
          `<div class="citation-chip" onclick="findAndOpenPaper('${s.paper_id}')">📄 Source: ${s.paper_id}</div>`
      )
      .join(" ");
  }

  msgDiv.innerHTML = `
    <div class="msg-avatar">${avatar}</div>
    <div class="msg-body">
      ${text.replace(/\n/g, "<br>")}
      ${sourcesHtml ? `<div style="margin-top:8px;">${sourcesHtml}</div>` : ""}
    </div>
  `;

  chatMessages.appendChild(msgDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function appendLoading() {
  const chatMessages = document.getElementById("chat-messages");
  const id = `loading-${Date.now()}`;
  const msgDiv = document.createElement("div");
  msgDiv.className = "msg bot";
  msgDiv.id = id;

  msgDiv.innerHTML = `
    <div class="msg-avatar">🤖</div>
    <div class="msg-body" style="font-style:italic; color:var(--text-muted);">
      Đang gọi Tool semantic_search_papers và truy vấn ChromaDB... 🔍
    </div>
  `;
  chatMessages.appendChild(msgDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return id;
}

function removeMessage(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function findAndOpenPaper(paperId) {
  const found = papersData.find((p) => p.paper_id === paperId);
  if (found) {
    openModal(found);
  } else {
    alert(`Thông tin tài liệu ID: ${paperId}`);
  }
}

function refreshData() {
  fetchPapers();
}
