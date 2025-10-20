from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="CMU Africa Academic Advisor",
    description="Academic advisor chatbot for CMU Africa",
    version="1.0.0"
)

class ChatRequest(BaseModel):
    question: str
    session_id: str = "default"

class ChatResponse(BaseModel):
    answer: str
    session_id: str

@app.get("/")
def root():
    return {"message": "CMU Africa Academic Advisor API is running!", "status": "healthy"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/chat")
def chat(request: ChatRequest):
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    if not google_api_key:
        raise HTTPException(status_code=500, detail="Google API key not configured")
    
    # Built-in knowledge about CMU Africa
    cmu_knowledge = """
    Carnegie Mellon University Africa (CMU-Africa) Information:
    
    MS IT Program Tracks:
    1. Professional Track - Focus on team project skills and industry experience
    2. Research Track - Focus on research and thesis work  
    3. Coursework Track - Focus on advanced coursework
    
    General Information:
    - Located in Kigali, Rwanda
    - Offers Master's programs in Information Technology and Electrical & Computer Engineering
    - Follows CMU's rigorous academic standards
    - Students typically take 36-48 units per semester
    - Academic integrity policies are strictly enforced
    - Career services and student support available
    
    Contact Information:
    - Academic Affairs: africa-academics@andrew.cmu.edu
    - Student Affairs: studentsupport-africa@andrew.cmu.edu
    - Admissions: africa-admissions@andrew.cmu.edu
    """
    
    # Prepare the prompt with built-in knowledge
    system_prompt = f"""You are an Academic Adviser assistant at Carnegie Mellon University Africa. 
    Use the following information to help answer student questions:
    
    {cmu_knowledge}
    
    If you don't have specific information, recommend contacting the appropriate office.
    """
    
    full_prompt = f"{system_prompt}\n\nStudent Question: {request.question}\n\nAnswer:"
    
    try:
        # Use Google Gemini API directly
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={google_api_key}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": full_prompt
                }]
            }]
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if "candidates" in result and len(result["candidates"]) > 0:
                answer = result["candidates"][0]["content"]["parts"][0]["text"]
                return ChatResponse(answer=answer, session_id=request.session_id)
            else:
                raise HTTPException(status_code=500, detail="No response from AI model")
        else:
            raise HTTPException(status_code=500, detail=f"AI API error: {response.text}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)