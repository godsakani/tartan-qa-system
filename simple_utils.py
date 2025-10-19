"""
Simplified version for free deployment without heavy ML dependencies
"""
import os
from typing import List, Dict, Any
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Simple in-memory document store
document_store = {}
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

def load_and_split_document(file_path: str) -> List[str]:
    """Load and split document into chunks"""
    if file_path.endswith('.pdf'):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith('.docx'):
        loader = Docx2txtLoader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path}")
    
    documents = loader.load()
    splits = text_splitter.split_documents(documents)
    return [doc.page_content for doc in splits]

def index_document_simple(file_path: str, file_id: int) -> bool:
    """Index document in simple in-memory store"""
    try:
        chunks = load_and_split_document(file_path)
        document_store[file_id] = chunks
        print(f"Successfully indexed {len(chunks)} chunks for file_id {file_id}")
        return True
    except Exception as e:
        print(f"Error indexing document: {e}")
        return False

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

def get_simple_rag_chain():
    """Get simple RAG chain without heavy dependencies"""
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
    
    def simple_rag_function(input_data):
        question = input_data["input"]
        chat_history = input_data.get("chat_history", [])
        
        # Simple search
        relevant_chunks = simple_search(question, k=5)
        context = "\n\n".join(relevant_chunks)
        
        # Build chat history
        history_str = ""
        if chat_history:
            for msg in chat_history:
                role = "Human" if msg["role"] == "human" else "Assistant"
                history_str += f"{role}: {msg['content']}\n"
        
        # Create prompt
        prompt = f"""You are an Academic Adviser assistant at Carnegie Mellon University Africa. Use the context below to answer student questions about courses, policies, and academic planning.

Context Information:
{context}

Chat History:
{history_str}

Student Question: {question}

Answer:"""
        
        try:
            response = gemini_model.generate_content(prompt)
            return {"answer": response.text}
        except Exception as e:
            return {"answer": f"I apologize, but I encountered an error: {str(e)}. Please try again."}
    
    return simple_rag_function

def delete_document_simple(file_id: int) -> bool:
    """Delete document from simple store"""
    if file_id in document_store:
        del document_store[file_id]
        return True
    return False