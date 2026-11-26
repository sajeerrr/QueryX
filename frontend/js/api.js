// Route to the FastAPI backend on port 8000 when served from a local static
// dev server (e.g. VS Code Live Server on :5500), and use the /api proxy
// when served behind Nginx/Docker.
const API = (() => {
    const { protocol, hostname, port } = window.location;
    if (protocol === "file:" || ["5500", "5501", "5502", "5173", "4173", "8080", "5000"].includes(port)) {
        const scheme = protocol === "file:" ? "http:" : protocol;
        return `${scheme}//${hostname || "127.0.0.1"}:8000/api`;
    }
    return "/api";
})();

// Generate a unique ID with a fallback for browsers that don't support crypto.randomUUID()
function generateId() {
    if (window.crypto && typeof window.crypto.randomUUID === "function") {
        return window.crypto.randomUUID();
    }

    return (
        Date.now().toString(36) +
        "-" +
        Math.random().toString(36).substring(2, 15)
    );
}

function getSessionId() {
    let sessionId = localStorage.getItem("queryx_session_id");

    if (!sessionId) {
        sessionId = generateId();
        localStorage.setItem("queryx_session_id", sessionId);
    }

    return sessionId;
}

function newSession() {
    const sessionId = generateId();
    localStorage.setItem("queryx_session_id", sessionId);
    return sessionId;
}

async function _readErrorDetail(response, fallback) {
    const errData = await response.json().catch(() => ({}));
    return errData.detail || `${fallback} (status ${response.status})`;
}

async function uploadDocument(file, { signal, uploadId } = {}) {
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
        if (error && error.name === "AbortError") {
            throw error;
        }
        console.error("[QueryX upload] request could not reach the backend", error);
        throw new Error("Could not connect to the upload API at " + API);
    }

    console.info("[QueryX upload] reliable upload response received", { status: response.status, ok: response.ok });
    if (!response.ok) {
        throw new Error(await _readErrorDetail(response, "Upload failed"));
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
        throw new Error(await _readErrorDetail(response, "Upload failed"));
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
        buffer = lines.pop();

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
        throw new Error(await _readErrorDetail(response, "Streaming request failed"));
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

async function askQuestion(question) {
    const response = await fetch(`${API}/chat`, {
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
        throw new Error(await _readErrorDetail(response, "Chat request failed"));
    }
    return response.json();
}

async function getDocuments() {
    const response = await fetch(`${API}/documents`);
    if (!response.ok) {
        throw new Error(await _readErrorDetail(response, "Failed to load documents"));
    }
    return response.json();
}

async function deleteDocument(id) {
    const response = await fetch(`${API}/documents/${encodeURIComponent(id)}`, {
        method: "DELETE"
    });
    if (!response.ok) {
        throw new Error(await _readErrorDetail(response, "Failed to delete document"));
    }
    return response.json();
}

function clearDocumentsOnUnload(documentIds = []) {
    const payload = JSON.stringify({
        session_id: getSessionId(),
        document_ids: documentIds,
        clear_all: true
    });
    const url = `${API}/documents/clear`;

    // text/plain avoids a CORS preflight request so sendBeacon succeeds during tab close.
    if (navigator.sendBeacon) {
        const blob = new Blob([payload], { type: "text/plain;charset=UTF-8" });
        if (navigator.sendBeacon(url, blob)) {
            return;
        }
    }

    fetch(url, {
        method: "POST",
        body: payload,
        keepalive: true
    }).catch(() => {});
}
