const documentContainer = document.getElementById("documents");

async function loadDocuments() {

    documentContainer.innerHTML = "Loading...";

    try {
        const docs = await getDocuments();
        documentContainer.innerHTML = "";

        if (docs.length === 0) {
            documentContainer.innerHTML = "<p>No documents uploaded.</p>";
            return;
        }

        docs.forEach(doc => {

            const card = document.createElement("div");
            card.className = "document-card";

            card.innerHTML = `
                <div class="document-name">
                    ${doc.filename}
                </div>

                <div class="document-meta">
                    ${doc.chunks} chunks
                </div>

                <button
                    class="delete-btn"
                    data-id="${doc.document_id}"
                >
                    Delete
                </button>
            `;

            documentContainer.appendChild(card);
        });

        addDeleteEvents();

    } catch (error) {

        console.error(error);
        documentContainer.innerHTML =
            "<p>Unable to load documents.</p>";
    }
}


function addDeleteEvents() {

    const buttons =
        document.querySelectorAll(".delete-btn");

    buttons.forEach(button => {

        button.addEventListener("click", async () => {
            const id = button.dataset.id;
            if (!confirm("Delete this document?"))
                return;

            await deleteDocument(id);
            loadDocuments();
        });
    });
}