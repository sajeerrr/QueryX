const messagesEl   = document.getElementById("messages");
const questionInput= document.getElementById("question");
const sendBtn      = document.getElementById("sendBtn");

function addMessage(text, type, sources) {
    const row = document.createElement("div");
    row.className = `message ${type}`;

    const av = document.createElement("div");
    av.className = `msg-avatar ${type === "ai" ? "ai" : "usr"}`;
    av.textContent = type === "ai" ? "Q" : "You";

    const bub = document.createElement("div");
    bub.className = "bubble";
    bub.textContent = text;

    if (sources && sources.length) {
        const sc = document.createElement("div");
        sc.className = "source-chips";
        sc.innerHTML = `<div class="source-chips-label">Sources</div>`;
        sources.forEach(s => {
            const chip = document.createElement("span");
            chip.className = "chip";
            chip.textContent = `📄 ${s.filename} · chunk ${s.chunk_id}`;
            sc.appendChild(chip);
        });
        bub.appendChild(sc);
    }

    row.appendChild(av);
    row.appendChild(bub);
    messagesEl.appendChild(row);
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

async function sendQuestion() {
    const q = questionInput.value.trim();
    if (!q) return;

    addMessage(q, "user");
    questionInput.value = "";
    sendBtn.disabled = true;

    let typingEl = null;
    try {
        typingEl = showTyping();
        const res = await askQuestion(q);
        typingEl.remove();
        addMessage(res.answer, "ai", res.sources || []);
    } catch (err) {
        if (typingEl) typingEl.remove();
        addMessage("Something went wrong. Is the server running?", "ai");
    } finally {
        sendBtn.disabled = false;
    }
}

sendBtn.addEventListener("click", sendQuestion);
questionInput.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendQuestion(); }
});

function showTyping() {
    const row = document.createElement("div");
    row.className = "message ai typing-bubble";
    row.innerHTML = `
        <div class="msg-avatar ai">Q</div>
        <div class="bubble"><div class="dot-row"><span></span><span></span><span></span></div></div>
    `;
    messagesEl.appendChild(row);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return row;
}
