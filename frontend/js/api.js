const API = "http://localhost:8000/api";


function getSessionId() {
    let sessionId = localStorage.getItem("queryx_session_id");

    if (!sessionId) {
        sessionId = crypto.randomUUID();
        localStorage.setItem("queryx_session_id", sessionId);
    }

    return sessionId;
}

function newSession() {
    const sessionId = crypto.randomUUID();
    localStorage.setItem("queryx_session_id", sessionId);
    return sessionId;
}


async function uploadDocument(file){

    const formData = new FormData();
    formData.append("file",file);
    const response = await fetch(`${API}/upload`,{
        method:"POST",
        body:formData
    });
    return response.json();
}


async function streamAnswer(question, onChunk) {
    const response = await fetch(`${API}/chat/stream`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            session_id: getSessionId(),
            question: question
        })
    });

    if (!response.ok) {
        throw new Error("Streaming request failed");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        onChunk(chunk);
    }
}


async function askQuestion(question){

    const response = await fetch(`${API}/chat`,{
        method:"POST",
        headers:{
            "Content-Type":"application/json"
        },
        body:JSON.stringify({
            session_id: getSessionId(),
            question: question
        })
    });
    return response.json();
}


async function getDocuments(){

    const response = await fetch(`${API}/documents`);
    return response.json();
}


async function deleteDocument(id){

    await fetch(`${API}/documents/${id}`,{
        method:"DELETE"
    });
}