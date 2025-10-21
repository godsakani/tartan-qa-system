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