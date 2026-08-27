const fileInput = document.getElementById("fileInput");
const uploadBtn = document.getElementById("uploadBtn");

uploadBtn.addEventListener("click", async () => {

    const file = fileInput.files[0];

    if (!file) {
        alert("Please select a PDF.");
        return;
    }

    uploadBtn.disabled = true;
    uploadBtn.textContent = "Uploading...";

    try {

        const result = await uploadDocument(file);

        alert(
            `Uploaded ${result.filename}\nIndexed ${result.indexed_chunks} chunks`
        );

        fileInput.value = "";

        loadDocuments();

    } catch (error) {

        console.error(error);

        alert("Upload failed.");

    } finally {

        uploadBtn.disabled = false;
        uploadBtn.textContent = "Upload";

    }

});