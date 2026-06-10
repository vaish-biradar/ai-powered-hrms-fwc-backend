from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse
import os
from dotenv import load_dotenv
import asyncio

# Utility functions
from prompts.candidate_resume_analysis_prompt import get_resume_analysis_prompt  # Resume analysis prompt
from prompts.hr_detailed_resume_report import get_detailed_resume_report_prompt  # Detailed report prompt
from utils.database import db  # Directly import db
from openaiservice.openaiclient import client  # OpenAI client initialization
from utils.logger_config import logger  # Logging configuration

# Load environment variables
load_dotenv()
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

# Define the router
analysis = APIRouter(prefix="/analysis", tags=["Analysis"])


@analysis.post("/candidate")
async def generate_analysis(data: dict):
    """
    Generates an AI-driven analysis of a candidate's resume against a job description (JD).
    """
    try:
        # Fetch resume and JD from the database
        resume = db.get("resumes", data["resume_id"])
        jd = db.get("jds", data["jd_id"])
        similarity=data["similarity"]
        jd_title=data["jd_title"]
        
        logger.info(f"similarity {similarity}")

        if not resume or not jd:
            return JSONResponse(status_code=404, content={"error": "Resume/JD not found"})

        # Prepare messages for the AI model
        messages = get_resume_analysis_prompt(jd["text"], resume["text"], float(similarity),jd_title)

        # Call Azure OpenAI API asynchronously
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=AZURE_OPENAI_DEPLOYMENT_NAME,  
            messages=messages,
            max_completion_tokens=1500,
            stream=True
        )

        # Stream response back to the client
        async def event_generator():
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta:
                    text = chunk.choices[0].delta.content if chunk.choices[0].delta.content is not None else ""
                    if text:
                        yield text  

        return StreamingResponse(event_generator(), media_type="text/plain")

    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return JSONResponse(status_code=500, content={"error": "Server error"})


@analysis.post("/hr")
async def generate_detailed_analysis(data: dict):
    """
    Generates a detailed AI-driven HR report comparing a candidate's resume against a job description.
    """
    try:
        # Fetch resume and JD from the database
        resume = db.get("resumes", data.get("resume_id"))
        jd = db.get("jds", data.get("jd_id"))

        if not resume or not jd:
            return JSONResponse(status_code=404, content={"error": "Resume/JD not found"})

        # Prepare messages for the AI model
        messages = get_detailed_resume_report_prompt(jd["text"], resume["text"])

        # Call Azure OpenAI API asynchronously
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=AZURE_OPENAI_DEPLOYMENT_NAME,  
            messages=messages,
            max_completion_tokens=1500,
            stream=True
        )

        # Stream response back to the client
        async def event_generator():
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta:
                    text = chunk.choices[0].delta.content if chunk.choices[0].delta.content is not None else ""
                    if text:
                        yield text  # Ensure proper spacing between chunks

        return StreamingResponse(event_generator(), media_type="text/plain")

    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return JSONResponse(status_code=500, content={"error": "Server error"})
