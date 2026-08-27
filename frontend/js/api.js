const API = "http://localhost:8000/api";

async function uploadDocument(file){

    const formData = new FormData();
    formData.append("file",file);
    const response = await fetch(`${API}/upload`,{
        method:"POST",
        body:formData
    });
    return response.json();
}

async function askQuestion(question){

    const response = await fetch(`${API}/chat`,{
        method:"POST",
        headers:{
            "Content-Type":"application/json"
        },
        body:JSON.stringify({
            question
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