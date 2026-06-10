from fastapi import APIRouter
from fastapi.responses import JSONResponse
import asyncio
import os
import re
from uuid import UUID
from prompts.match_resume_to_jds import get_match_resume_to_jds  # Prompt generator for resume-to-JD matching
from prompts.match_jd_to_resumes import get_match_jd_to_resumes  # Prompt generator for JD-to-resume matching
from dotenv import load_dotenv
from utils.database import db  # Directly import db
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta,timezone
from openaiservice.openaiclient import client  # OpenAI client for LLM interaction
from utils.logger_config import logger  # Logging configuration
from schemas.models import MatchRequest, JDMatchRequest,CompareRequest  # Request models
from urllib.parse import urlparse,unquote
from utils.file_utils import generate_sas_url
load_dotenv()
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
CONNECTION_STRING = os.getenv("STORAGE_ACCOUNT_CONNECTION_STRING")
RESUME_CONTAINER_NAME = os.getenv("RESUME_CONTAINER_NAME")
STORAGE_ACCOUNT_KEY=os.getenv("STORAGE_ACCOUNT_KEY")



match = APIRouter(prefix="/match", tags=["Match"])

@match.post("/resume-to-jds")
async def match_resume(request: MatchRequest):
    """Matches a resume to all available job descriptions (JDs) and returns the best matches."""
    try:
        resume = db.get("resumes", request.resume_id)
        if not resume:
            return JSONResponse(status_code=404, content={"error": "Resume not found"})

        jds = db.get_all("jds")
        if not jds:
            return JSONResponse(status_code=404, content={"error": "No JDs found"})

        # Filter JDs with status 'Open'
        open_jds = [jd for jd in jds if jd.get("status") == "Open"]

        async def fetch_relevance(jd):
            """Fetches similarity score between a resume and a JD using an LLM."""
            messages = get_match_resume_to_jds(resume["text"], jd["text"])
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=messages,
                temperature=0.5,
                max_completion_tokens=500
            )
            
            content_str = response.choices[0].message.content if response.choices else "{}"
            similarity = float(content_str)
            
            return {
                "jd_id": jd["id"],
                "jd_title": jd["title"],
                "similarity": similarity,
                "jd_text": jd["text"]
            }

        # Run all similarity calculations concurrently for only 'Open' JDs
        results = await asyncio.gather(*(fetch_relevance(jd) for jd in open_jds))

        # Return matches sorted by similarity score (descending)
        return sorted(results, key=lambda x: x["similarity"], reverse=True)

    except Exception as e:
        logger.error(f"Matching error: {e}")
        return JSONResponse(status_code=500, content={"error": "Server error"})







@match.post("/jd-to-resumes")
async def match_jd(request: JDMatchRequest):  
    """Matches a job description (JD) to all available resumes and returns the best matches."""
    try:
        logger.info(request.apply_filter)
        apply_filter = request.apply_filter
        logger.info(apply_filter)
        jd_id = UUID(request.jd_id)
        jd = db.get("jds", jd_id)
        if not jd:
            return JSONResponse(status_code=404, content={"error": "JD not found"})

        resumes = db.get_all("resumes")
        if not resumes:
            return JSONResponse(status_code=404, content={"error": "No resumes found"})

        jd_title_normalized = re.sub(r"\s+", "", jd["title"].lower())

        # Apply filtering only if apply_filter is True
        if apply_filter:
            resumes = [
                resume for resume in resumes
                if any(
                    re.sub(r"\s+", "", role.lower()) in jd_title_normalized
                    or jd_title_normalized in re.sub(r"\s+", "", role.lower())
                    for role in resume.get("suitable_roles", [])
                )
            ]

        async def fetch_relevance(resume):
            """Fetches similarity score between a JD and a resume using an LLM."""
            messages = get_match_jd_to_resumes(jd["text"], resume["text"])
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=messages,
                temperature=0.5,
                max_completion_tokens=500
            )
            
            ai_response = response.choices[0].message.content  
            similarity = float(ai_response)
            logger.info(f"Resume {resume['id']} - Score: {similarity}")
            return similarity

        async def process_resume(resume):
            """Processes a single resume by computing similarity and extracting key details."""
            similarity = await fetch_relevance(resume)
            resume_url = await generate_sas_url(resume['path'],RESUME_CONTAINER_NAME)
            return {
                "resume_id": str(resume["id"]),
                "name": resume["name"],
                "email": resume["email"],
                "phone": resume.get("phone", "Not Available"),
                "similarity": similarity,
                "resume_text": resume["text"],
                "path": resume_url,
            }

        # Run similarity calculations concurrently
        results = await asyncio.gather(*(process_resume(resume) for resume in resumes))

        # Sort results by similarity score (descending)
        sorted_matches = sorted(results, key=lambda x: x["similarity"], reverse=True)

        return JSONResponse(content=sorted_matches, status_code=200)

    except Exception as e:
        logger.error(f"JD matching error: {e}")
        return JSONResponse(status_code=500, content={"error": "Server error"})
    
    


@match.post("/compare-candidates")
async def compare_candidates(request: CompareRequest):
    """Compares all selected candidate resumes against a job description in one LLM prompt and ranks them."""
    try:
        jd_id = UUID(request.jd_id)
        candidate_ids = request.candidates  # List of resume IDs (UUIDs)
        logger.info(candidate_ids)
        logger.info(jd_id)
        
        jd = db.get("jds", jd_id)
        if not jd:
            return JSONResponse(status_code=404, content={"error": "JD not found"})
        
        resumes = db.get_all("resumes")
        if not resumes:
            return JSONResponse(status_code=404, content={"error": "No resumes found"})
        
        # Filter only the selected candidates
        candidate_resumes = [r for r in resumes if str(r["id"]) in candidate_ids]
        
        if not candidate_resumes:
            return JSONResponse(status_code=404, content={"error": "Selected candidates not found"})
        
        # Format all resumes
        formatted_resumes = ""
        for idx, r in enumerate(candidate_resumes, 1):
            formatted_resumes += f""" 
### Candidate {idx}: {r['name']}
- **Email:** {r['email']}
- **Phone:** {r.get('phone', 'Not Available')}
- **Resume Text:** {r['text']}

"""
        
        messages = [
    {
        "role": "system",
        "content": """
You are a highly experienced talent acquisition specialist. Your task is to evaluate candidate resumes against a job description and identify the best-fit candidates using structured and data-driven analysis.

Only use markdown **tables** to present your results. Focus on clarity, conciseness, and actionable insights.
"""
    },
    {
        "role": "user",
        "content": f"""
# 🧠 Resume Evaluation Task

Evaluate the candidate resumes below against the job description. Present your analysis **only using markdown tables**, structured in the following sections:


## 📊 Candidate Comparison Table

| Candidate Name | Match Score (1-100) | Relevant Experience (yrs) | Key Strengths | Areas of Concern |
|----------------|--------------------|---------------------------|---------------|------------------|
| (Auto-fill all rows for each candidate) |


## 📋 Individual Candidate Analysis

| Candidate | Summary | Matching Qualifications | Missing Skills | Cultural Fit |
|-----------|---------|-------------------------|----------------|---------------|
| (Add a row for each candidate with brief yet specific entries) |


## 🏆 Ranking & Recommendations

| Rank | Candidate | Recommendation (Interview/Shortlist/Reject) | Justification |
|------|-----------|---------------------------------------------|---------------|
| 1    |           |                                             |               |
| 2    |           |                                             |               |
| ...  |           |                                             |               |


use Job Description  from below
{jd['text']}

 use Candidate Resumes   from below
{formatted_resumes}
"""
    }
]

        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=messages,
            temperature=0.3,  # Lower temperature for more structured output
            max_completion_tokens=3000,  # Increased token limit for more detailed analysis
        )
        
        markdown = response.choices[0].message.content
        
        return JSONResponse(content={"markdown": markdown}, status_code=200)
    
    except Exception as e:
        logger.error(f"Comparison error: {e}")
        return JSONResponse(status_code=500, content={"error": "Server error"})