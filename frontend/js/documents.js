/* documents.js — Load existing documents from API and sync with file list */

async function loadDocuments() {
    try {
        const docs = await getDocuments();
        if (docs && docs.length > 0) {
            // Sync server documents into local state
            uploadedFiles = docs.map(d => ({
                id: d.document_id,
                name: d.filename,
                chunks: d.chunks || '—'
            }));
            renderFileList();

            // Auto-select first document and show chat
            showView('Chat');
            addWelcomeAfterUpload(uploadedFiles[0].name);
        }
    } catch (e) {
        // Server might not be running — silently fail
        console.log("loadDocuments: server not reachable", e.message);
    }
}

// Run after DOM is ready (scripts load at end of body)
loadDocuments();
