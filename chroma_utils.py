# from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredHTMLLoader
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_community.embeddings import GooglePalmEmbeddings
# from langchain_openai import OpenAIEmbeddings
# from langchain_chroma import Chroma
# from typing import List
# from langchain_core.documents import Document
# import os
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()

# # Check if API key exists
# openai_api_key = os.getenv("GOOGLE_API_KEY")
# if not openai_api_key:
#     raise ValueError("OPENAI_API_KEY environment variable is not set. Please set it in your .env file or environment variables.")

# #Initialize text splitter and embedding function
# text_splitter = RecursiveCharacterTextSplitter(chunk_size =1000, chunk_overlap=200, length_function=len)
# #embedding_function = OpenAIEmbeddings(openai_api_key=openai_api_key)
# embedding_function = GooglePalmEmbeddings(openai_api_key=openai_api_key)

# # Initializing Chroma vector store
# vectorstore =Chroma(persist_directory="./chroma_db", embedding_function=embedding_function)


# def load_and_split_document(file_path:str)->List[Document]:
#     if file_path.endswith('.pdf'):
#         loader = PyPDFLoader(file_path)
#     elif file_path.endswith('.docx'):
#         loader = Docx2txtLoader(file_path)
#     elif file_path.endswith('.html'):
#         loader = UnstructuredHTMLLoader(file_path) 
#     else:
#         raise ValueError(f"Unsupported file type: {file_path}")
    
    
#     documents = loader.load()
#     return text_splitter.split_documents(documents)


# def index_document_to_chroma(file_path:str, file_id:int)->bool:
#     try:
#        splits = load_and_split_document(file_path)
#        # Add metadata to each split
#        for split in splits:
#            split.metadata['file_id'] = file_id
           
#        vectorstore.add_documents(splits)
#        return True
#     except Exception as e:
#         print(f"Error indexing document: {e}")
#         return False
    
# def delete_doc_from_chroma(file_id: int):
#     try:
#         docs = vectorstore.get(where={"file_id":file_id})
#         print(f"Found {len(docs['ids'])} document chunks for file_id {file_id}") 
        
#         vectorstore._collection.delete(where={"file_id":file_id})
#         print(f"Deleted all documents with file_id {file_id}")
        
#         return True
#     except Exception as e:
#         print(f"Error deleting document with file_id {file_id} from Chroma: {str(e)}")
#         return False
    
# #retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
## Google Embeddings
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredHTMLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from typing import List
from langchain_core.documents import Document
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize text splitter and embedding function
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len)

# Use HuggingFace embeddings (free and reliable)
embedding_function = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)

# Use persistent storage path for production
DATA_DIR = os.getenv("DATA_DIR", "./data")
CHROMA_DIR = os.path.join(DATA_DIR, "chroma_db")
os.makedirs(CHROMA_DIR, exist_ok=True)

vectorstore = Chroma(persist_directory=CHROMA_DIR, embedding_function=embedding_function)

def load_and_split_document(file_path: str) -> List[Document]:
    if file_path.endswith('.pdf'):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith('.docx'):
        loader = Docx2txtLoader(file_path)
    elif file_path.endswith('.html'):
        loader = UnstructuredHTMLLoader(file_path) 
    else:
        raise ValueError(f"Unsupported file type: {file_path}")
    
    documents = loader.load()
    return text_splitter.split_documents(documents)

def index_document_to_chroma(file_path: str, file_id: int) -> bool:
    try:
        splits = load_and_split_document(file_path)
        # Add metadata to each split
        for split in splits:
            split.metadata['file_id'] = file_id
            
        vectorstore.add_documents(splits)
        print(f"Successfully indexed {len(splits)} document chunks for file_id {file_id}")
        return True
    except Exception as e:
        print(f"Error indexing document: {e}")
        return False
    
def delete_doc_from_chroma(file_id: int) -> bool:
    try:
        # Get documents with the specific file_id
        docs = vectorstore.get(where={"file_id": file_id})
        print(f"Found {len(docs['ids'])} document chunks for file_id {file_id}") 
        
        # Delete documents with the specific file_id
        if docs['ids']:
            vectorstore.delete(ids=docs['ids'])
            print(f"Deleted all documents with file_id {file_id}")
        else:
            print(f"No documents found with file_id {file_id}")
        
        return True
    except Exception as e:
        print(f"Error deleting document with file_id {file_id} from Chroma: {str(e)}")
        return False

# retriever = vectorstore.as_retriever(search_kwargs={"k": 2})