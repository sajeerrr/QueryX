// Use the same loopback host as the page (127.0.0.1 in the local UI) rather
// than mixing localhost and 127.0.0.1 across browser/network configurations.
const API = `${window.location.protocol}//${window.location.hostname}:8000/api`;


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


async function uploadDocument(file, { signal, uploadId } = {}){

    const formData = new FormData();
    formData.append("file", file);
    console.info("[QueryX upload] sending reliable upload request", {
        name: file.name,
        bytes: file.size,
        endpoint: `${API}/upload`
    });
    let response;
    try {
        response = await fetch(`${API}/upload`, {
            method: "POST",
            body: formData,
            signal,
            headers: uploadId ? { "X-Upload-Id": uploadId } : undefined
        });
    } catch (error) {
        console.error("[QueryX upload] request could not reach the backend", error);
        throw new Error("Could not connect to the upload API at " + API);
    }
    console.info("[QueryX upload] reliable upload response received", { status: response.status, ok: response.ok });
    if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Upload failed with status ${response.status}`);
    }
    const result = await response.json();
    console.info("[QueryX upload] indexing completed", result);
    return result;
}

async function cancelDocumentUpload(uploadId) {
    if (!uploadId) return;

    await fetch(`${API}/upload/cancel/${encodeURIComponent(uploadId)}`, {
        method: "POST"
    });
}


async function uploadDocumentStream(file, onProgress) {
    const formData = new FormData();
    formData.append("file", file);
    console.info("[QueryX upload] sending file", {
        name: file.name,
        bytes: file.size,
        endpoint: `${API}/upload/stream`
    });

    let response;
    try {
        response = await fetch(`${API}/upload/stream`, {
            method: "POST",
            body: formData
        });
    } catch (error) {
        console.error("[QueryX upload] request could not reach the backend", error);
        throw new Error("Could not connect to the upload API at " + API);
    }

    console.info("[QueryX upload] backend response received", { status: response.status, ok: response.ok });

    if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Upload failed with status ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";
    let finalResult = null;

    while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop(); // keep last unfinished piece

        for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed) continue;
            try {
                const event = JSON.parse(trimmed);
                console.info("[QueryX upload] progress event", event);
                if (event.stage === "error") {
                    throw new Error(event.message || "Document processing failed");
                }
                if (typeof onProgress === "function") {
                    onProgress(event);
                }
                if (event.stage === "complete") {
                    finalResult = event;
                }
            } catch (err) {
                if (err.message && !err.message.includes("JSON")) {
                    throw err;
                }
            }
        }
    }

    if (!finalResult) {
        console.error("[QueryX upload] stream ended without a complete event");
        throw new Error("Document processing ended prematurely.");
    }

    console.info("[QueryX upload] completed", finalResult);
    return finalResult;
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
