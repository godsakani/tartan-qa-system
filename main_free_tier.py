from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic_models import QueryInput, QueryResponse, DocumentInfo, DeleFileRequest
from db_utils import insert_application_logs, get_chat_history, get_all_documents, insert_document_record, delete_document_record
import os
import uuid
import logging
import shutil
import google.generativeai as genai
from dotenv import load_dotenv
import PyPDF2
from docx import Document
import re
from typing import List, Dict

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)

# Initialize FastAPI app
app = FastAPI(
    title="RAG Academic Advisor API",
    description="Academic advisor chatbot for CMU Africa using Google Gemini",
    version="1.0.0"
)

# Simple in-memory document store (since we can't use ChromaDB)
document_store: Dict[int, List[str]] = {}

def simple_text_splitter(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """Simple text splitter without dependencies"""
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        if end > text_len:
            end = text_len
        
        chunk = text[start:end]
        chunks.append(chunk.strip())
        
        start = end - chunk_overlap
        if start >= text_len:
            break
    
    return [chunk for chunk in chunks if chunk.strip()]

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF"""
    text = ""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        raise ValueError(f"Error reading PDF: {e}")
    return text

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX"""
    text = ""
    try:
        doc = Document(file_path)
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
    except Exception as e:
        raise ValueError(f"Error reading DOCX: {e}")
    return text

def simple_search(query: str, k: int = 5) -> List[str]:
    """Simple keyword-based search"""
    results = []
    query_lower = query.lower()
    
    for file_id, chunks in document_store.items():
        for chunk in chunks:
            chunk_lower = chunk.lower()
            # Simple scoring based on keyword matches
            score = 0
            for word in query_lower.split():
                if word in chunk_lower:
                    score += chunk_lower.count(word)
            
            if score > 0:
                results.append((score, chunk))
    
    # Sort by score and return top k
    results.sort(key=lambda x: x[0], reverse=True)
    return [chunk for _, chunk in results[:k]]

def get_gemini_response(question: str, context: str, chat_history: List[Dict]) -> str:
    """Get response from Google Gemini"""
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    if not google_api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not set")
    
    # Configure Google AI
    genai.configure(api_key=google_api_key)
    
    # Use available Gemini model
    try:
        gemini_model = genai.GenerativeModel('models/gemini-2.5-flash')
    except:
        try:
            gemini_model = genai.GenerativeModel('models/gemini-2.0-flash')
        except:
            gemini_model = genai.GenerativeModel('models/gemini-flash-latest')
    
    # Build chat history
    history_str = ""
    if chat_history:
        for msg in chat_history:
            role = "Human" if msg["role"] == "human" else "Assistant"
            history_str += f"{role}: {msg['content']}\n"
    
    # Create prompt
    prompt = f"""You are an Academic Adviser assistant at Carnegie Mellon University Africa. You help students with questions about course registration, academic policies, degree requirements, and academic planning.

Use the context below to answer student questions. If the context contains relevant information, use it to provide a comprehensive answer. If you don't have specific information, provide general guidance and suggest contacting the academic advising office.

Context Information:
{context}

Chat History:
{history_str}

Student Question: {question}

Answer:"""
    
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"I apologize, but I encountered an error: {str(e)}. Please try again or contact the academic advising office directly."

@app.get("/")
def root():
    return {"message": "RAG Academic Advisor API is running!", "status": "healthy"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/chat", response_model=QueryResponse)
def chat(query_input: QueryInput):
    session_id = query_input.session_id or str(uuid.uuid4())
    logging.info(f"Session ID: {session_id}, User Query: {query_input.question}")
    
    try:
        chat_history = get_chat_history(session_id)
        
        # Search for relevant context
        relevant_chunks = simple_search(query_input.question, k=5)
        context = "\n\n".join(relevant_chunks) if relevant_chunks else "No specific context available."
        
        # Get AI response
        answer = get_gemini_response(query_input.question, context, chat_history)
        
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
        
        # Extract text based on file type
        if file_extension == '.pdf':
            text = extract_text_from_pdf(temp_file_path)
        elif file_extension == '.docx':
            text = extract_text_from_docx(temp_file_path)
        
        # Clean and split text
        text = re.sub(r'\s+', ' ', text).strip()
        if not text:
            raise HTTPException(status_code=400, detail="No text content found in document")
        
        chunks = simple_text_splitter(text)
        
        # Store in database and memory
        file_id = insert_document_record(file.filename)
        document_store[file_id] = chunks
        
        logging.info(f"Successfully indexed {len(chunks)} chunks for file_id {file_id}")
        return {"message": f"File {file.filename} uploaded successfully with ID: {file_id}"}
        
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
        # Remove from memory store
        if request.file_id in document_store:
            del document_store[request.file_id]
        
        # Remove from database
        db_delete_success = delete_document_record(request.file_id)
        
        if db_delete_success:
            return {"message": f"Document with ID {request.file_id} deleted successfully"}
        else:
            return {"error": f"Failed to delete document with ID {request.file_id}"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/debug-search")
def debug_search(query: str = "MS IT tracks"):
    """Debug endpoint to test search functionality"""
    try:
        results = simple_search(query, k=5)
        return {
            "total_documents": len(document_store),
            "search_query": query,
            "results_count": len(results),
            "results": [{"content_preview": result[:200] + "..."} for result in results]
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)