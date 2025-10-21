
# from langchain_openai import ChatOpenAI
# from langchain_core.output_parsers import StrOutputParser
# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langchain.chains.history_aware_retriever import create_history_aware_retriever
# from langchain.chains.retrieval import create_retrieval_chain
# from langchain.chains.combine_documents.stuff import create_stuff_documents_chain
# from typing import List
# from langchain_core.documents import Document
# import os
# from chroma_utils import vectorstore


# retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
# output_parser = StrOutputParser()


# contextualize_q_system_prompt = (
#     "Given a chat history and the latest user question "
#     "which might reference context in the chat history, "
#     "formulate a standalone question which can be understood "
#     "without the chat history. Do NOT answer the question, "
#     "just reformulate it if needed and otherwise return it as is."
# )

# contextualize_q_prompt = ChatPromptTemplate.from_messages([
#     ("system", contextualize_q_system_prompt),
#     MessagesPlaceholder("chat_history"),
#     ("human", "{input}"),
# ])

# qa_prompt = ChatPromptTemplate.from_messages([
#     ("system", """You are assign the role of Academic Adviser assistant at Carnegie Mellon University Africa, you have more knowledge about Courses registration at CMU Africa, accademic policies, use of AI in academics. Your  role is to understand and answer student queries like course registration, units, Academy policies, and questions related to courses and degree planning at CMU Africa.
#     your job is to answer the Student queries with the information you are provided with."""),
#     ("system", "Context: {context}"),
#     MessagesPlaceholder(variable_name="chat_history"),
#     ("human", "{input}")
# ])

# def get_rag_chain(model="gpt-4o-mini"):
#     llm = ChatOpenAI(model=model)
#     history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)
#     question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
#     rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
#     return rag_chain

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables from parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from chroma_utils import vectorstore

retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

contextualize_q_system_prompt = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, "
    "just reformulate it if needed and otherwise return it as is."
)

contextualize_q_prompt = ChatPromptTemplate.from_messages([
    ("system", contextualize_q_system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are assigned the role of Academic Adviser assistant at Carnegie Mellon University Africa. You have extensive knowledge about Courses registration at CMU Africa, academic policies, and the use of AI in academics. Your role is to understand and answer student queries like course registration, units, academic policies, and questions related to courses and degree planning at CMU Africa.
    Your job is to answer the Student queries with the information you are provided with. If you don't know the answer based on the context provided, say that you don't know and suggest they contact the academic advising office directly."""),
    ("system", "Context: {context}"),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])

def get_rag_chain(model="gpt-4o-2024-08-06"):
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    llm = ChatOpenAI(model=model, openai_api_key=openai_api_key,
                     base_url='https://ai-gateway.andrew.cmu.edu/'
                     )
    
    # Create contextualized question chain
    contextualize_q_chain = contextualize_q_prompt | llm | StrOutputParser()
    
    def contextualized_question(input: Dict[str, Any]):
        if input.get("chat_history"):
            question = contextualize_q_chain.invoke({
                "chat_history": input["chat_history"],
                "input": input["input"]
            })
            return question
        else:
            return input["input"]
    
    # Create the full RAG chain
    rag_chain = (
        {
            "context": RunnablePassthrough.assign(
                question=RunnableLambda(contextualized_question)
            ) | (lambda x: retriever.invoke(x["question"])),
            "input": lambda x: x["input"],
            "chat_history": lambda x: x.get("chat_history", [])
        }
        | qa_prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain


# from langchain_core.output_parsers import StrOutputParser
# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langchain_core.runnables import RunnablePassthrough, RunnableLambda
# from typing import List, Dict, Any
# import os
# from dotenv import load_dotenv
# import google.generativeai as genai

# # Load environment variables
# load_dotenv()

# from chroma_utils import vectorstore

# retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

# def get_rag_chain(model="gemini-1.5-pro"):
#     google_api_key = os.getenv("GOOGLE_API_KEY")
    
#     if not google_api_key:
#         raise ValueError("GOOGLE_API_KEY environment variable is not set. Please get it from https://makersuite.google.com/app/apikey")
    
#     # Configure Google AI
#     genai.configure(api_key=google_api_key)
    
#     # List available models for debugging
#     try:
#         available_models = [m.name for m in genai.list_models()]
#         print(f"Available models: {available_models}")
#     except Exception as e:
#         print(f"Could not list models: {e}")
    
#     # Use Gemini model - try available models from the list
#     try:
#         # Try the latest flash model first
#         gemini_model = genai.GenerativeModel('models/gemini-2.5-flash')
#     except Exception as e1:
#         try:
#             # Try the 2.0 flash model
#             gemini_model = genai.GenerativeModel('models/gemini-2.0-flash')
#         except Exception as e2:
#             try:
#                 # Try the flash latest alias
#                 gemini_model = genai.GenerativeModel('models/gemini-flash-latest')
#             except Exception as e3:
#                 # Fallback to any available generative model
#                 try:
#                     available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
#                     if available_models:
#                         # Filter for flash models first, then any model
#                         flash_models = [m for m in available_models if 'flash' in m.lower()]
#                         model_name = flash_models[0] if flash_models else available_models[0]
#                         print(f"Using fallback model: {model_name}")
#                         gemini_model = genai.GenerativeModel(model_name)
#                     else:
#                         raise Exception("No suitable models found")
#                 except Exception as e4:
#                     raise Exception(f"Could not initialize any Gemini model. Errors: {e1}, {e2}, {e3}, {e4}")
    
#     def simple_rag_chain(input_data):
#         question = input_data["input"]
#         chat_history = input_data.get("chat_history", [])
        
#         # Get relevant documents using multiple search strategies
#         try:
#             # For MS IT track questions, search specifically for relevant terms
#             if "MS IT" in question or "MSIT" in question or "track" in question.lower():
#                 # Search for specific terms that we know exist
#                 search_terms = ["MSIT curriculum offers three tracks", "Master of Science in Information Technology", "Professional Track", "MSIT tracks"]
#                 docs = []
#                 for term in search_terms:
#                     search_results = vectorstore.similarity_search(term, k=3)
#                     docs.extend(search_results)
                
#                 # Remove duplicates while preserving order
#                 seen = set()
#                 unique_docs = []
#                 for doc in docs:
#                     doc_id = id(doc)  # Use object id as unique identifier
#                     if doc_id not in seen:
#                         seen.add(doc_id)
#                         unique_docs.append(doc)
#                 docs = unique_docs[:5]  # Limit to 5 documents
            
#             # If still no results or not an MS IT question, try general search
#             if not docs:
#                 docs = vectorstore.similarity_search(question, k=5)
                
#             # If still no results, try with different keywords
#             if not docs:
#                 search_terms = ["MS IT", "Master", "tracks", "Information Technology", "CMU Africa"]
#                 for term in search_terms:
#                     docs = vectorstore.similarity_search(term, k=3)
#                     if docs:
#                         break
#         except:
#             # Fallback to retriever
#             docs = retriever.invoke(question)
        
#         # Debug: Print retrieved documents info
#         print(f"Question: {question}")
#         print(f"Retrieved {len(docs)} documents:")
#         for i, doc in enumerate(docs):
#             source = doc.metadata.get('source', doc.metadata.get('file_id', 'Unknown source'))
#             print(f"Doc {i+1}: Source: {source}")
#             print(f"Content preview: {doc.page_content[:300]}...")
#             print("---")
        
#         context = "\n\n".join([doc.page_content for doc in docs])
        
#         # Debug: Print the full context being sent to AI
#         print(f"CONTEXT BEING SENT TO AI:")
#         print(f"Context length: {len(context)} characters")
#         print(f"Context content: {context[:1000]}...")
#         print("=" * 50)
        
#         # Build chat history string
#         history_str = ""
#         if chat_history:
#             for msg in chat_history:
#                 role = "Human" if msg["role"] == "human" else "Assistant"
#                 history_str += f"{role}: {msg['content']}\n"
        
#         # Create prompt
#         prompt = f"""You are an Academic Adviser assistant at Carnegie Mellon University Africa. You have extensive knowledge about course registration, academic policies, degree programs, and student services at CMU Africa.

# Your job is to provide helpful and accurate answers based on the context provided below. Use the information in the context to answer student questions about courses, degree requirements, tracks, policies, and academic planning.

# If the context contains relevant information, use it to provide a comprehensive answer. Only say you don't know if the context truly doesn't contain any relevant information about the question asked.

# Context Information:
# {context}

# Chat History:
# {history_str}

# Student Question: {question}

# Answer:"""
        
#         try:
#             response = gemini_model.generate_content(prompt)
#             return {"answer": response.text}
#         except Exception as e:
#             return {"answer": f"I apologize, but I encountered an error processing your request: {str(e)}. Please try again or contact the academic advising office directly."}
    
#     return simple_rag_chain