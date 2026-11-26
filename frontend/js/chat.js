const messagesEl   = document.getElementById("messages");
const questionInput= document.getElementById("question");
const sendBtn      = document.getElementById("sendBtn");

// Simple markdown to HTML renderer
function renderMarkdown(text) {
    if (!text) return '';

    // Escape HTML first
    let html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    // Protect code blocks and inline code before running emphasis rules
    const codeTokens = [];
    html = html.replace(/```([\s\S]*?)```/g, (_, code) => {
        const token = `\u0000CODE${codeTokens.length}\u0000`;
        codeTokens.push(`<pre><code>${code}</code></pre>`);
        return token;
    });
    html = html.replace(/`([^`\n]+)`/g, (_, code) => {
        const token = `\u0000CODE${codeTokens.length}\u0000`;
        codeTokens.push(`<code>${code}</code>`);
        return token;
    });

    // Bold: **text** or __text__
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/__(.*?)__/g, '<strong>$1</strong>');

    // Italic: *text* or _text_
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    html = html.replace(/_(.*?)_/g, '<em>$1</em>');

    // Line breaks
    html = html.replace(/\n/g, '<br>');

    // Restore protected code spans
    html = html.replace(/\u0000CODE(\d+)\u0000/g, (_, index) => codeTokens[Number(index)]);

    return html;
}

function addMessage(text, type, sources) {
    const row = document.createElement("div");
    row.className = `message ${type}`;

    const av = document.createElement("div");
    av.className = `msg-avatar ${type === "ai" ? "ai" : "usr"}`;
    av.textContent = type === "ai" ? "Q" : "You";

    const bub = document.createElement("div");
    bub.className = "bubble";
    bub.innerHTML = renderMarkdown(text);

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

    // ── Remove initial welcome card when user starts chatting ──
    const welcomeCard = document.getElementById("welcomeCard");
    if (welcomeCard) {
        welcomeCard.remove();
    }

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
            bubble.innerHTML = renderMarkdown(answer);

            messagesEl.scrollTop = messagesEl.scrollHeight;
        });

    } catch (err) {

        typingEl.remove();
        row.remove();

        addMessage(err?.message || "Something went wrong.", "ai");

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
