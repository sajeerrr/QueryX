/* documents.js — Load existing documents from API and sync with file list */

let _documentsLoaded = false;

async function loadDocuments() {
    try {
        const docs = await getDocuments();
        _documentsLoaded = true;

        if (docs && Array.isArray(docs)) {
            // Preserve any in-flight optimistic uploads (temp IDs start with '__')
            const inFlightUploads = (typeof uploadedFiles !== 'undefined' ? uploadedFiles : [])
                .filter(f => f.id && String(f.id).startsWith('__'));

            // Build server document list
            const serverFiles = docs.map(d => ({
                id: d.document_id,
                name: d.filename,
                chunks: d.chunks || '—',
                uploading: false,
                active: false
            }));

            // Merge: server docs first, then any in-flight uploads
            uploadedFiles = [...serverFiles, ...inFlightUploads];

            if (uploadedFiles.length > 0) {
                // Ensure at least one active document
                const activeDoc = uploadedFiles.find(f => f.active);
                if (!activeDoc) {
                    uploadedFiles[0].active = true;
                }
                renderFileList();

                // If no upload in progress, show chat view with welcome message
                if (inFlightUploads.length === 0) {
                    showView('Chat');
                    if (typeof showWelcomeView === 'function') {
                        showWelcomeView();
                    }
                }
            } else {
                renderFileList();
                showView('Upload');
            }
        }
    } catch (e) {
        _documentsLoaded = true;
        console.log("loadDocuments: server not reachable", e.message);
        if (typeof uploadedFiles !== 'undefined' && uploadedFiles.length === 0) {
            showView('Upload');
        }
    }
}

// Run when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadDocuments);
} else {
    loadDocuments();
}

