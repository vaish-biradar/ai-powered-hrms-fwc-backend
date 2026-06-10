from fastapi import APIRouter, UploadFile, File, HTTPException
from starlette import status
import os
import json
import asyncio
import uuid
import datetime
from sqlmodel import Session, select

# custom imports
from openaiservice.openaiclient import client
from prompts.trnascripts_prompt import get_transcripts_prompt
from prompts.mock_interview_prompt import get_mock_interview_messages
from schemas.models import MockInterviewChatRequest, MockInterviewSaveRequest, TranscriptTextRequest
from utils.database import db, Resume, JobDescription, MockInterview

transcript_analysis = APIRouter(prefix="/transcript", tags=["Transcript Processing"])
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")


def _clean_json_response(raw: str) -> dict:
    cleaned = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(cleaned)

@transcript_analysis.post("/process", status_code=status.HTTP_200_OK)
async def process_transcript(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="File is required")
    
    # Read the file contents directly from memory
    try:
        extracted_text = (await file.read()).decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

    # Call OpenAI client
    try:
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT_NAME,  
            messages=get_transcripts_prompt(extracted_text),
            max_completion_tokens=1000
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing text: {str(e)}")

    # Return the response
    return {"response": response.choices[0].message.content}


@transcript_analysis.post("/analyze-text", status_code=status.HTTP_200_OK)
async def analyze_transcript_text(payload: TranscriptTextRequest):
    transcript_text = (payload.transcript_text or "").strip()
    if not transcript_text:
        raise HTTPException(status_code=400, detail="Transcript text is required")

    try:
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=get_transcripts_prompt(transcript_text),
            max_completion_tokens=1000,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing text: {str(e)}")

    content = response.choices[0].message.content or ""
    try:
        return {"response": _clean_json_response(content)}
    except Exception:
        return {"response": content}


@transcript_analysis.post("/mock-interview/chat", status_code=status.HTTP_200_OK)
async def mock_interview_chat(payload: MockInterviewChatRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database is not initialized")

    try:
        resume = db.get("resumes", payload.resume_id)
        jd = db.get("jds", payload.jd_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid resume or JD id: {str(e)}")

    if not resume or not jd:
        raise HTTPException(status_code=404, detail="Resume or JD not found")

    conversation = [{"role": m.role, "content": m.content} for m in payload.messages if m.content.strip()]
    messages = get_mock_interview_messages(jd.get("text") or jd.get("description") or "", resume.get("text") or "", conversation)

    try:
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=messages,
            temperature=0.4,
            max_completion_tokens=400,
        )

        content = response.choices[0].message.content or ""
        parsed = _clean_json_response(content)
        reply = str(parsed.get("reply", "Can you share more about your recent project work?"))
        should_end = bool(parsed.get("should_end", False))
        return {"reply": reply, "should_end": should_end}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mock interview failed: {str(e)}")


@transcript_analysis.post("/mock-interview/save", status_code=status.HTTP_200_OK)
async def save_mock_interview(payload: MockInterviewSaveRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database is not initialized")

    jd = db.get("jds", payload.jd_id)
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")

    conversation = [{"role": m.role, "content": m.content} for m in payload.conversation if m.content.strip()]
    if not conversation:
        raise HTTPException(status_code=400, detail="Conversation is empty")

    transcript_text = "\n".join([f"{item['role'].upper()}: {item['content']}" for item in conversation])
    interview_id = uuid.uuid4()

    try:
        parsed_jd_id = uuid.UUID(payload.jd_id)
        parsed_resume_id = uuid.UUID(payload.resume_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid resume_id or jd_id")

    with Session(db.engine) as session:
        interview = MockInterview(
            id=interview_id,
            resume_id=parsed_resume_id,
            job_description_id=parsed_jd_id,
            candidate_name=payload.candidate_name,
            candidate_email=payload.candidate_email,
            transcript_text=transcript_text,
            conversation=conversation,
            status="completed",
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )
        session.add(interview)
        session.commit()

    return {"id": str(interview_id), "message": "Mock interview saved"}


@transcript_analysis.get("/mock-interviews", status_code=status.HTTP_200_OK)
async def get_mock_interviews():
    if db is None:
        raise HTTPException(status_code=500, detail="Database is not initialized")

    with Session(db.engine) as session:
        statement = (
            select(MockInterview, JobDescription)
            .join(JobDescription, MockInterview.job_description_id == JobDescription.id)
            .order_by(MockInterview.created_at.desc())
        )
        rows = session.exec(statement).all()

        result = []
        for interview, jd in rows:
            result.append(
                {
                    "id": str(interview.id),
                    "candidate_name": interview.candidate_name,
                    "candidate_email": interview.candidate_email,
                    "job_title": jd.title,
                    "created_at": interview.created_at.isoformat() if interview.created_at else None,
                    "transcript_text": interview.transcript_text,
                    "conversation": interview.conversation,
                }
            )

    return result