import sys
import os
from dotenv import load_dotenv

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic_models import QueryInput, QueryResponse, DocumentInfo, DeleFileRequest
from langchain_utils import get_rag_chain
from db_utils import insert_application_logs, get_chat_history,get_all_documents, insert_document_record, delete_document_record
from chroma_utils import index_document_to_chroma, delete_doc_from_chroma
import uuid
import logging
import shutil


#Set up logging
logging.basicConfig(filename='app.log', level=logging.INFO)

#initializing FastAPI app
app = FastAPI(
    title="RAG Academic Advisor API",
    description="Academic advisor chatbot for CMU Africa using RAG",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"message": "RAG Academic Advisor API is running!", "status": "healthy"}

@app.get("/health")
def health_check():
    return {"status": "healthy"} 

@app.post("/chat", response_model=QueryResponse)
def chat(query_input:QueryInput):
    session_id = query_input.session_id or str(uuid.uuid4())
    logging.info(f"Session ID: {session_id}, User Query: {query_input.question}, Model: {query_input.model.value}")
    
    chat_history = get_chat_history(session_id)
    rag_chain = get_rag_chain(query_input.model.value)
    result = rag_chain.invoke({
        "input":query_input.question,
        "chat_history":chat_history
    })
    
    # Handle both string and dictionary responses
    logging.info(f"RAG chain result type: {type(result)}")
    if isinstance(result, dict):
        answer = result.get('answer', str(result))
    else:
        answer = str(result)
    
    insert_application_logs(session_id, query_input.question, answer, query_input.model.value)
    logging.info(f"Session ID: {session_id}, AI Response: {answer}")
    return QueryResponse(answer=answer, session_id=session_id, model=query_input.model)

@app.post("/upload-doc")
def upload_and_index_document(file:UploadFile=File(...)):
    allowed_extensions = ['.pdf', '.docx', '.html']
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"File type not supported. File must be: {', '.join(allowed_extensions)}")
    
    temp_file_path = f"temp_{file.filename}"
    
    
    try:
        #Save the uploaded file to a temporary file
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        file_id = insert_document_record(file.filename)
        success = index_document_to_chroma(temp_file_path, file_id)
        
        if success:
            return {"message": f"File {file.filename} uploaded successful with file Id: {file_id}"}
        else:
            delete_doc_from_chroma(file_id)
            raise HTTPException(status_code=500, detail=f"Failed to index {file.filename}.")
        
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@app.get("/all-docs", response_model=list[DocumentInfo])
def all_docs():
    return get_all_documents()

@app.get("/debug-search")
def debug_search(query: str = "MS IT tracks"):
    from chroma_utils import vectorstore
    
    # Get all documents in the collection
    try:
        all_docs = vectorstore.get()
        total_docs = len(all_docs['ids']) if all_docs['ids'] else 0
        
        # Search for documents
        search_results = vectorstore.similarity_search(query, k=5)
        
        return {
            "total_documents_in_vectorstore": total_docs,
            "search_query": query,
            "search_results_count": len(search_results),
            "search_results": [
                {
                    "content_preview": doc.page_content[:200] + "...",
                    "metadata": doc.metadata
                }
                for doc in search_results
            ]
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/clear-vectorstore")
def clear_vectorstore():
    """Clear all documents from the vector store"""
    from chroma_utils import vectorstore
    
    try:
        # Get all documents
        all_docs = vectorstore.get()
        
        if all_docs['ids']:
            # Delete all documents
            vectorstore.delete(ids=all_docs['ids'])
            return {"message": f"Successfully deleted {len(all_docs['ids'])} documents from vector store"}
        else:
            return {"message": "Vector store is already empty"}
            
    except Exception as e:
        return {"error": f"Failed to clear vector store: {str(e)}"}

@app.post("/delete-doc")
def delete_document(request:DeleFileRequest):
    chroma_delete_success = delete_doc_from_chroma(request.file_id)
    
    if chroma_delete_success:
        db_delete_success = delete_document_record(request.file_id)
        if db_delete_success:
            return {"message": f"Document deleted Successful with id {request.file_id} from the system"}
        else:
            return {"error":f"Delete document from chroma but failed to delete with file_id {request.file_id} from the database."}
    else:
        return {"error":f"Failed to delete document with file_id {request.file_id} from chroma."}