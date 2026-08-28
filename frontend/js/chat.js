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

    // Step 1: Show typing animation
    const typingEl = showTyping();

    // Step 2: Prepare assistant message (hidden for now)
    const row = document.createElement("div");
    row.className = "message ai";
    row.style.display = "none";

    const av = document.createElement("div");
    av.className = "msg-avatar ai";
    av.textContent = "Q";

    const bubble = document.createElement("div");
    bubble.className = "bubble";

    row.appendChild(av);
    row.appendChild(bubble);
    messagesEl.appendChild(row);

    let answer = "";
    let firstChunk = true;

    try {

        await streamAnswer(q, (chunk) => {

            // First token received
            if (firstChunk) {

                typingEl.remove();

                row.style.display = "flex";

                firstChunk = false;
            }

            answer += chunk;
            bubble.textContent = answer;

            messagesEl.scrollTop = messagesEl.scrollHeight;
        });

    } catch (err) {

        typingEl.remove();
        row.remove();

        addMessage("Something went wrong.", "ai");

        console.error(err);

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
