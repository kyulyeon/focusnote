"""
Meeting Transcript Processing Microservice
FastAPI service for generating summaries, minutes, and action items from meeting transcripts
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from pydantic import BaseModel, Field
from typing import Optional, List
import google.generativeai as genai
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Meeting Transcript Service",
    description="Process meeting transcripts to generate summaries, minutes, and action items",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY not found in environment variables")
else:
    genai.configure(api_key=GEMINI_API_KEY)

# Models
class TranscriptRequest(BaseModel):
    transcript: str = Field(..., description="The meeting transcript text")
    meeting_title: Optional[str] = Field(None, description="Optional meeting title")
    meeting_date: Optional[str] = Field(None, description="Optional meeting date")
    participants: Optional[List[str]] = Field(None, description="Optional list of participants")

class SummaryResponse(BaseModel):
    summary: str
    meeting_title: Optional[str]
    meeting_date: Optional[str]
    processed_at: str

class MinutesResponse(BaseModel):
    minutes: str
    meeting_title: Optional[str]
    meeting_date: Optional[str]
    participants: Optional[List[str]]
    processed_at: str

class ActionItemsResponse(BaseModel):
    action_items: List[str]
    meeting_title: Optional[str]
    meeting_date: Optional[str]
    processed_at: str

# Helper function to call Gemini API
async def call_gemini(prompt: str, max_retries: int = 3) -> str:
    """Call Gemini API with retry logic"""
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")
    
    for attempt in range(max_retries):
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini API call failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt == max_retries - 1:
                raise HTTPException(status_code=500, detail=f"Failed to generate content: {str(e)}")
    
    raise HTTPException(status_code=500, detail="Failed to generate content after retries")

# Endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Meeting Transcript Service",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    gemini_configured = GEMINI_API_KEY is not None
    return {
        "status": "healthy",
        "gemini_api_configured": gemini_configured,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/v1/summary", response_model=SummaryResponse)
async def generate_summary(request: TranscriptRequest):
    """
    Generate a concise summary of the meeting transcript
    """
    logger.info(f"Generating summary for transcript (length: {len(request.transcript)})")
    
    prompt = f"""
    Please provide a concise summary of the following meeting transcript. 
    Focus on the main topics discussed, key decisions made, and overall themes.
    Keep the summary clear and actionable.
    
    Meeting Transcript:
    {request.transcript}
    
    Provide only the summary without any preamble.
    """
    
    summary = await call_gemini(prompt)
    
    return SummaryResponse(
        summary=summary.strip(),
        meeting_title=request.meeting_title,
        meeting_date=request.meeting_date,
        processed_at=datetime.utcnow().isoformat()
    )

@app.post("/api/v1/minutes", response_model=MinutesResponse)
async def generate_minutes(request: TranscriptRequest):
    """
    Generate formal meeting minutes from the transcript
    """
    logger.info(f"Generating minutes for transcript (length: {len(request.transcript)})")
    
    prompt = f"""
    Please generate formal meeting minutes from the following transcript.
    Structure the minutes with:
    - Opening/Context
    - Discussion Points (organized by topic)
    - Decisions Made
    - Next Steps
    
    Meeting Transcript:
    {request.transcript}
    
    Provide the minutes in a professional format suitable for distribution.
    """
    
    minutes = await call_gemini(prompt)
    
    return MinutesResponse(
        minutes=minutes.strip(),
        meeting_title=request.meeting_title,
        meeting_date=request.meeting_date,
        participants=request.participants,
        processed_at=datetime.utcnow().isoformat()
    )

@app.post("/api/v1/action-items", response_model=ActionItemsResponse)
async def generate_action_items(request: TranscriptRequest):
    """
    Extract action items from the meeting transcript
    """
    logger.info(f"Generating action items for transcript (length: {len(request.transcript)})")
    
    prompt = f"""
    Please extract all action items from the following meeting transcript.
    For each action item, include:
    - What needs to be done
    - Who is responsible (if mentioned)
    - When it needs to be completed (if mentioned)
    
    Format each action item as a single clear statement.
    If no action items are found, return "No action items identified."
    
    Meeting Transcript:
    {request.transcript}
    
    Provide only the list of action items, one per line, without numbering or bullets.
    """
    
    action_items_text = await call_gemini(prompt)
    
    # Parse action items into a list
    action_items = [
        item.strip() 
        for item in action_items_text.strip().split('\n') 
        if item.strip() and not item.strip().startswith('#')
    ]
    
    return ActionItemsResponse(
        action_items=action_items,
        meeting_title=request.meeting_title,
        meeting_date=request.meeting_date,
        processed_at=datetime.utcnow().isoformat()
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8888))
    uvicorn.run(app, host="127.0.0.1", port=port)