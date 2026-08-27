const messages = document.getElementById("messages");
const questionInput = document.getElementById("question");
const sendBtn = document.getElementById("sendBtn");


function addMessage(text, type) {

    const wrapper = document.createElement("div");

    wrapper.className = `message ${type}`;

    const bubble = document.createElement("div");

    bubble.className = "bubble";

    bubble.textContent = text;

    wrapper.appendChild(bubble);

    messages.appendChild(wrapper);

    messages.scrollTop = messages.scrollHeight;

}


async function sendQuestion() {

    const question = questionInput.value.trim();

    if (!question)
        return;

    addMessage(question, "user");

    questionInput.value = "";

    sendBtn.disabled = true;

    try {
        showTyping();
        const response = await askQuestion(question);
        hideTyping();
        let answer = response.answer;

        if (response.sources?.length) {
            answer += "\n\nSources:\n";
            response.sources.forEach(source => {
                answer +=
                    `• ${source.filename} (Chunk ${source.chunk_id})\n`;
            });
        }
        addMessage(answer, "ai");
    }

    catch (err) {

        console.error(err);

        addMessage(
            "Something went wrong.",
            "ai"
        );

    }

    finally {

        sendBtn.disabled = false;

    }

}


sendBtn.addEventListener(
    "click",
    sendQuestion
);

questionInput.addEventListener(
    "keydown",
    (e) => {

        if (e.key === "Enter") {

            sendQuestion();

        }

    }
);

let typingMessage = null;

function showTyping(){

    typingMessage = document.createElement("div");

    typingMessage.className = "message ai";

    typingMessage.innerHTML =
        '<div class="bubble">Thinking...</div>';

    messages.appendChild(typingMessage);

    messages.scrollTop = messages.scrollHeight;

}

function hideTyping(){

    if(typingMessage){

        typingMessage.remove();

        typingMessage = null;

    }

}