from fastapi import UploadFile, File, HTTPException, APIRouter, Request, Query
from fastapi.responses import JSONResponse
import os
import hashlib
from dotenv import load_dotenv
import uuid
import asyncio
from datetime import datetime,timezone# Utility functions
from utils.file_utils import save_file, extract_text_from_file,delete_blob,generate_sas_url
from prompts.job_details_prompt import get_job_details_prompt
from openaiservice.openaiclient import client  # Initialize OpenAI
from utils.logger_config import logger  # Logging configuration
from urllib.parse import urlparse,unquote
from schemas.models import CancelRequest  # Import the CancelRequest model
load_dotenv()
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
from utils.database import db  # Directly import db
JD_CONTAINER_NAME = os.getenv("JD_CONTAINER_NAME")

jd = APIRouter(prefix="/jd", tags=["Jd"])

JD_CONTAINER_NAME = os.getenv("JD_CONTAINER_NAME")
@jd.post("/create")
async def create_jd(files: list[UploadFile] = File(...)):
    """Upload and process job descriptions."""
    try:
        async def process_file(file):
            jd_url = await save_file(file, JD_CONTAINER_NAME)
            jd_text = await extract_text_from_file(JD_CONTAINER_NAME, jd_url)
            if not jd_text:
                return {"error": f"Failed to extract text from {file.filename}"}

            jd_id = uuid.uuid4()
         

            messages = get_job_details_prompt(jd_text)
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=messages,
                max_completion_tokens=500
            )

            job_title, job_department, job_type, job_location, job_experience, job_summary, job_skills = (
                "Unknown Title", "Unknown Department", "Unknown Type", "Unknown Location", "Unknown Experience", 
                "No summary available", "No skills listed"
            )

            if response and response.choices:
                ai_response = response.choices[0].message.content.strip()
                lines = ai_response.split("\n")

                for line in lines:
                    if "Title:" in line:
                        job_title = line.replace("Title:", "").strip().lstrip("*").strip()
                    elif "Department:" in line:
                        job_department = line.replace("Department:", "").strip().lstrip("*").strip()
                    elif "Employment Type:" in line:
                        job_type = line.replace("Employment Type:", "").strip().lstrip("*").strip()
                    elif "Location:" in line:
                        job_location = line.replace("Location:", "").strip().lstrip("*").strip()
                    elif "Experience Level:" in line:
                        job_experience = line.replace("Experience Level:", "").strip().lstrip("*").strip()
                    elif "Summary:" in line:
                        job_summary = line.replace("Summary:", "").strip().lstrip("*").strip()
                    elif "Required Skills:" in line:
                        job_skills = line.replace("Required Skills:", "").strip().lstrip("*").strip()

            logger.info(f"Job Title: {job_title}, Location: {job_location}")

            db.insert("jds", {
                "id":jd_id,
                "title":job_title.strip(),
                "department":job_department.strip(),
                "employment_type":job_type.strip(),
                "location":job_location.strip(),
                "experience_level":job_experience.strip(),
                "summary":job_summary.strip(),
                "skills":job_skills.strip(),
                "path":jd_url.strip(),
                "text":jd_text.strip(),
                "created_date":datetime.now(timezone.utc).isoformat(),
                "status":"Open",
                "total_openings":0,
                "occupied_openings":0
            })


            return {"id": jd_id, "title": job_title, "summary": job_summary}

        results = await asyncio.gather(*(process_file(file) for file in files))
        return results[0] if len(results) == 1 else {"jds": results}

    except Exception as e:
        logger.error(f"JD creation error: {e}")
        return JSONResponse(status_code=500, content={"error": "Server error"})
    
@jd.put("/update/{jd_id}")
async def update_jd(jd_id: str, request: Request):
    body = await request.json()
    logger.info(f"Raw Request Body: {body}")

    update_data = {}
    if "status" in body:
        update_data["status"] = body["status"]
    if "occupied_openings" in body and body["occupied_openings"] is not None:
        update_data["occupied_openings"] = body["occupied_openings"]
    if "total_openings" in body and body["total_openings"] is not None:
        update_data["total_openings"] = body["total_openings"]

    if not update_data:
        return JSONResponse(status_code=400, content={"error": "No data provided for update"})

    db.update("jds", jd_id, update_data)

    return {"message": "JD updated successfully"}

@jd.post("/extract")
async def extract_jd(files: list[UploadFile] = File(...)):
    """Upload and extract job description details without saving to database."""
    try:
        async def process_file(file):
            # Save file to blob storage
            jd_url = await save_file(file, JD_CONTAINER_NAME)
            jd_text = await extract_text_from_file(JD_CONTAINER_NAME, jd_url)
            
            if not jd_text:
                return {"error": f"Failed to extract text from {file.filename}"}
                
            jd_id = str(uuid.uuid4())
            
            # Get job details using AI
            messages = get_job_details_prompt(jd_text)
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=messages,
                max_completion_tokens=500
            )
            
            # Default values
            job_title, job_department, job_type, job_location = "Unknown Title", "Unknown Department", "Unknown Type", "Unknown Location"
            job_experience, job_summary, job_skills = "Unknown Experience", "No summary available", "No skills listed"
            
            # Parse AI response
            if response and response.choices:
                ai_response = response.choices[0].message.content.strip()
                lines = ai_response.split("\n")
                
                for line in lines:
                    if "Title:" in line:
                        job_title = line.replace("Title:", "").strip().lstrip("*").strip()
                    elif "Department:" in line:
                        job_department = line.replace("Department:", "").strip().lstrip("*").strip()
                    elif "Employment Type:" in line:
                        job_type = line.replace("Employment Type:", "").strip().lstrip("*").strip()
                    elif "Location:" in line:
                        job_location = line.replace("Location:", "").strip().lstrip("*").strip()
                    elif "Experience Level:" in line:
                        job_experience = line.replace("Experience Level:", "").strip().lstrip("*").strip()
                    elif "Summary:" in line:
                        job_summary = line.replace("Summary:", "").strip().lstrip("*").strip()
                    elif "Required Skills:" in line:
                        job_skills = line.replace("Required Skills:", "").strip().lstrip("*").strip()
            
            logger.info(f"Extracted Job Title: {job_title}, Location: {job_location}")
            
            # Return extracted data without saving to DB
            return {
                "id": jd_id,
                "title": job_title.strip(),
                "department": job_department.strip(),
                "employment_type": job_type.strip(), 
                "location": job_location.strip(),
                "experience_level": job_experience.strip(),
                "summary": job_summary.strip(),
                "skills": job_skills.strip(),
                "path": jd_url.strip(),
                "text": jd_text.strip(),
                "temp_file_path": jd_url  # Include the path for potential deletion
            }
        
        results = await asyncio.gather(*(process_file(file) for file in files))
        return results[0] if len(results) == 1 else {"jds": results}
        
    except Exception as e:
        logger.error(f"JD extraction error: {e}")
        return JSONResponse(status_code=500, content={"error": "Server error during extraction"})


@jd.post("/save")
async def save_jd(jd_data: dict):
    """Save or update job description details to database."""
    try:
        # Check if we have all required fields
        required_fields = ["id", "title", "department", "employment_type", "location", 
                          "experience_level", "summary", "skills", "path", "text"]
        
        if not all(field in jd_data for field in required_fields):
            return JSONResponse(
                status_code=400, 
                content={"error": "Missing required fields in job description data"}
            )
        
        jd_id = jd_data["id"]
        logger.info(f"JD User: {jd_data.get("user", {})}")
        # Insert into database with additional fields
        db.insert("jds", {
            "id": jd_id,
            "title": jd_data["title"].strip(),
            "department": jd_data["department"].strip(),
            "employment_type": jd_data["employment_type"].strip(),
            "location": jd_data["location"].strip(),
            "experience_level": jd_data["experience_level"].strip(),
            "summary": jd_data["summary"].strip(),
            "skills": jd_data["skills"].strip(),
            "path": jd_data["path"].strip(),
            "text": jd_data["text"].strip(),
            "created_date": datetime.now(timezone.utc).isoformat(),
            "submitted_by": jd_data.get("user", {}),
            "status": "Open",
            "total_openings": 0,
            "occupied_openings": 0
        })
        
        return {"id": jd_id, "title": jd_data["title"], "status": "saved"}
        
    except Exception as e:
        logger.error(f"JD save error: {e}")
        return JSONResponse(status_code=500, content={"error": "Server error during save"})





@jd.delete("/cancel")
async def cancel_jd(cancel_data: CancelRequest):
    """Delete uploaded file from blob storage when user cancels the operation."""
    try:
        file_path = cancel_data.file_path
        logger.info(f"Attempting to delete file: {file_path}")
        
        # Handle the URL-encoded path
        if file_path.startswith('http'):
            # Extract just the blob name from the URL 
            from urllib.parse import urlparse
            parsed_url = urlparse(file_path)
            path = parsed_url.path
            if path.startswith('/'):
                path = path[1:]  # Remove leading slash
                
            # Extract the blob name after the container name
            parts = path.split('/', 1)
            if len(parts) > 1:
                blob_name = parts[1]
            else:
                blob_name = file_path  # Fallback
        else:
            blob_name = file_path
            
        logger.info(f"Extracted blob name: {blob_name}")
        
        # Delete the file from blob storage
        deleted = await delete_blob(JD_CONTAINER_NAME, blob_name)
        
        if deleted:
            return {"status": "deleted", "path": file_path}
        else:
            return JSONResponse(status_code=404, content={"error": "File not found"})
            
    except Exception as e:
        logger.error(f"JD cancel error: {e}")
        return JSONResponse(status_code=500, content={"error": "Server error during cancellation"})

@jd.get("/get-all")
async def get_all_jds():
    """Retrieve all job descriptions."""
    try:
        jds = db.get_all("jds")
        if not jds:
            return JSONResponse(status_code=200, content=[])




        extracted_jds = [
            {
                "id": jd["id"],
                "title": jd["title"],
                "text": jd["text"],
                "summary": jd["summary"],
                "path": await generate_sas_url(jd["path"], JD_CONTAINER_NAME),
                "created_at": jd["created_at"],
                "total_openings": jd["total_openings"],
                "occupied_openings": jd["occupied_openings"],
                "status": jd["status"],  # Added missing comma
                "department": jd["department"],
                "employment_type": jd["employment_type"],
                "location": jd["location"],
                "experience_level": jd["experience_level"],  # Fixed incorrect closing bracket
                "skills": jd["skills"],  # Fixed incorrect list structure
                "submitted_by": jd["submitted_by"]
            }
            for jd in jds
        ]

        return extracted_jds
    except Exception as e:
        logger.error(f"Error fetching JDs: {e}")
        return JSONResponse(status_code=500, content={"error": "Server error"})

@jd.get("/get/{jd_id}")
async def get_jd(jd_id: str):
    """Retrieve a specific job description by ID."""
    jd = db.get("jds", jd_id)
    if not jd:
        raise HTTPException(status_code=404, detail="JD not found")
    return jd

@jd.delete("/delete/{jd_id}")
async def delete_jd(jd_id: str):
    """Delete a job description by ID."""
    
    
    jd_data = db.get("jds",jd_id)
    if not jd_data:
        raise HTTPException(status_code=404, detail="JD not found")
    
    jd_url = jd_data["path"]
    
    blob_name = urlparse(jd_url).path.split("/")[-1]
    decoded_blob_name = unquote(blob_name)
    
    
    deleted = db.delete("jds", jd_id)
    
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete resume from database")
    
    result =await delete_blob(JD_CONTAINER_NAME, decoded_blob_name)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    
    return {"message": f"Resume '{jd_id}' and blob deleted successfully!"}



