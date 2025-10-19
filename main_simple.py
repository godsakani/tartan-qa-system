from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic_models import QueryInput, QueryResponse, DocumentInfo, DeleFileRequest
from simple_utils import get_simple_rag_chain, index_document_simple, delete_document_simple
from db_utils import insert_application_logs, get_chat_history, get_all_documents, insert_document_record, delete_document_record
import os
import uuid
import logging
import shutil

# Set up logging
logging.basicConfig(level=logging.INFO)

# Initialize FastAPI app
app = FastAPI(
    title="RAG Academic Advisor API (Simple)",
    description="Lightweight academic advisor chatbot for CMU Africa",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"message": "RAG Academic Advisor API (Simple) is running!", "status": "healthy"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/chat", response_model=QueryResponse)
def chat(query_input: QueryInput):
    session_id = query_input.session_id or str(uuid.uuid4())
    logging.info(f"Session ID: {session_id}, User Query: {query_input.question}")
    
    try:
        chat_history = get_chat_history(session_id)
        rag_chain = get_simple_rag_chain()
        result = rag_chain({
            "input": query_input.question,
            "chat_history": chat_history
        })
        answer = result['answer']
        
        insert_application_logs(session_id, query_input.question, answer, query_input.model.value)
        logging.info(f"Session ID: {session_id}, AI Response generated")
        return QueryResponse(answer=answer, session_id=session_id, model=query_input.model)
    
    except Exception as e:
        logging.error(f"Error in chat: {e}")
        return QueryResponse(
            answer="I apologize, but I'm experiencing technical difficulties. Please try again later.",
            session_id=session_id,
            model=query_input.model
        )

@app.post("/upload-doc")
def upload_and_index_document(file: UploadFile = File(...)):
    allowed_extensions = ['.pdf', '.docx']
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"File type not supported. Supported: {', '.join(allowed_extensions)}")
    
    temp_file_path = f"temp_{file.filename}"
    
    try:
        # Save the uploaded file temporarily
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        file_id = insert_document_record(file.filename)
        success = index_document_simple(temp_file_path, file_id)
        
        if success:
            return {"message": f"File {file.filename} uploaded successfully with ID: {file_id}"}
        else:
            delete_document_record(file_id)
            raise HTTPException(status_code=500, detail=f"Failed to index {file.filename}")
        
    except Exception as e:
        logging.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.get("/all-docs", response_model=list[DocumentInfo])
def all_docs():
    return get_all_documents()

@app.post("/delete-doc")
def delete_document(request: DeleFileRequest):
    try:
        simple_delete_success = delete_document_simple(request.file_id)
        db_delete_success = delete_document_record(request.file_id)
        
        if db_delete_success:
            return {"message": f"Document with ID {request.file_id} deleted successfully"}
        else:
            return {"error": f"Failed to delete document with ID {request.file_id}"}
    except Exception as e:
        return {"error": str(e)}