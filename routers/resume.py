from fastapi import UploadFile, File, HTTPException, APIRouter
from fastapi.responses import JSONResponse
import os
import hashlib
import json
import asyncio
import re
from dotenv import load_dotenv
from typing import List,Tuple
import uuid
# Utility functions
from utils.file_utils import save_file, extract_text_from_file, delete_blob
from prompts.name_email_extraction import get_name_email_extraction_prompt
from openaiservice.openaiclient import client  # OpenAI client
from utils.logger_config import logger  # Logging configuration
from urllib.parse import urlparse, unquote

# Import the new PostgreSQL database client
from utils.database import db  # Adjusted import to use the new PostgreSQL client
from utils.database import Application  # Import the Application model

# Load environment variables
load_dotenv()
HR_EMAIL = os.getenv("HR_EMAIL")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
RESUME_CONTAINER_NAME = os.getenv("RESUME_CONTAINER_NAME")

resume = APIRouter(prefix="/resume", tags=["Resume"])
async def validate_resume_with_openai(text: str) -> Tuple[bool, str]:
    try:
        messages = [
            {"role": "system", "content": "You are a resume validator. Only judge based on the content of the text, not metadata or formatting issues."},
            {"role": "user", "content": f"""Does the following text appear to be a valid resume?

Only consider whether the text itself resembles a resume (e.g., mentions of experience, education, skills, projects, etc.).

Text:
{text}

Reply 'Yes' if it appears to be a resume. If not, explain why it isn't in a maximum of 10 words.(like Because ...)"""}
        ]

        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=messages,
            temperature=0.2,
            max_completion_tokens=200,
        )

        reply = response.choices[0].message.content.strip()
        if "yes" in reply.lower():
            return True, reply

        # Extract and clean the reason
        reason = reply.split("\n")[0].strip()
        warning = f"Reason: {reason}"
        return False, warning

    except Exception as e:
        return False, f"Validation error: {str(e)}"



# Extract Name & Email from Resume Text
async def extract_name_email(text: str):
    """
    Uses OpenAI to extract name and email from resume text.
    Returns extracted name and email, or defaults if extraction fails.
    """
    try:
        messages = get_name_email_extraction_prompt(text)
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=messages,
            max_completion_tokens=500,
        )

        ai_response = response.choices[0].message.content.strip()
        clean_response = re.sub(r"```json|```", "", ai_response)

        extracted_data = json.loads(clean_response)
        logger.info(extracted_data)

        # Ensure all expected keys exist in the response
        name = extracted_data.get("name", "Unknown Candidate")
        email = extracted_data.get("email", "Unknown Email")
        phone = extracted_data.get("phone", "Unknown Phone")
        suitable_roles = extracted_data.get("suitable_roles", [])
        summary = extracted_data.get("summary", "No summary available")
        experience_status = extracted_data.get("experience_status", "Fresher")
        years_of_experience = extracted_data.get("years_of_experience", "0 years")

        return name, email, phone, suitable_roles, summary, experience_status, years_of_experience

    except (json.JSONDecodeError, AttributeError, KeyError, IndexError) as e:
        logger.error(f"Error extracting name and email: {e}")
        return "Unknown Candidate", "Unknown Email", "Unknown Phone", [], "No summary available", "Fresher", "0 years"


# Upload a Single Resume
@resume.post("/upload-resume", response_model=dict)
async def upload_resume(file: UploadFile = File(...)):
    try:
        if not file:
            raise HTTPException(status_code=400, detail="File is required")

        resume_url = await save_file(file, RESUME_CONTAINER_NAME)
        text = await extract_text_from_file(RESUME_CONTAINER_NAME, resume_url)
        if not text:
            return JSONResponse(status_code=400, content={"error": "Text extraction failed"})
        is_resume, validation_feedback = await validate_resume_with_openai(text)
        if not is_resume:
            logger.info(f"Invalid resume: {validation_feedback}")
            # Optional: Delete the blob if it's not a valid resume
            await delete_blob(RESUME_CONTAINER_NAME, resume_url)  # optional cleanup
            return JSONResponse(
                status_code=200,  # Returning 200 OK with a warning
                content={
                    "warning": f"{validation_feedback}",
                    "id": None,
                }
            )
        resume_id = uuid.uuid4()
        extracted_name, extracted_email, extracted_phone, suitable_roles, extracted_summary, extracted_experience_status, extracted_years_of_experience = await extract_name_email(text)

        # If a resume with the same email exists, do not insert — inform the client.
        if extracted_email and extracted_email != "Unknown Email":
            existing_resume = db.find_one("resumes", {"email": extracted_email})
            if existing_resume:
                # Delete the newly uploaded blob to avoid orphaned files
                new_blob_name = urlparse(resume_url).path.split("/")[-1]
                decoded_new_blob_name = unquote(new_blob_name)
                await delete_blob(RESUME_CONTAINER_NAME, decoded_new_blob_name)

                return JSONResponse(
                    status_code=200,
                    content={
                        "id": str(existing_resume["id"]),
                        "message": "Resume already exists. Upload skipped.",
                    }
                )

        # No existing resume found — store new resume
        db.insert("resumes", {
            "id": resume_id,
            "name": extracted_name,
            "email": extracted_email,
            "phone": extracted_phone,
            "summary": extracted_summary,
            "experience_status": extracted_experience_status,
            "years_of_experience": extracted_years_of_experience,
            "suitable_roles": suitable_roles,
            "path": resume_url,
            "text": text
        })

        return {
            "id": str(resume_id),
            "message": "Resume uploaded successfully!"
        }

    except Exception as e:
        logger.error(f"Upload error: {e}")
        return JSONResponse(status_code=500, content={"error": f"Server error: {str(e)}"})


# Upload Multiple Resumes
@resume.post("/upload-resumes", response_model=dict)
async def upload_resumes(files: List[UploadFile] = File(...)):
    """
    Uploads multiple resumes, extracts text, identifies names and emails, and stores them in the database.
    Returns a list of successfully uploaded resumes.
    """
    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required")

    uploaded_resumes = []

    for file in files:
        try:
            resume_url = await save_file(file, RESUME_CONTAINER_NAME)
            text = await extract_text_from_file(RESUME_CONTAINER_NAME, resume_url)
            if not text:
                logger.warning(f"Skipping {file.filename} due to text extraction failure.")
                continue

            resume_id = uuid.uuid4()
            extracted_name, extracted_email, extracted_phone, suitable_roles, extracted_summary, extracted_experience_status, extracted_years_of_experience = await extract_name_email(text)

            # If a resume with the same email exists, skip and delete uploaded blob
            if extracted_email and extracted_email != "Unknown Email":
                existing_resume = db.find_one("resumes", {"email": extracted_email})
                if existing_resume:
                    new_blob_name = urlparse(resume_url).path.split("/")[-1]
                    decoded_new_blob_name = unquote(new_blob_name)
                    await delete_blob(RESUME_CONTAINER_NAME, decoded_new_blob_name)
                    uploaded_resumes.append({
                        "id": str(existing_resume["id"]),
                        "name": extracted_name,
                        "email": extracted_email,
                        "message": "Resume already exists. Upload skipped."
                    })
                    continue

            # Store in database
            db.insert("resumes", {
                "id": resume_id,
                "name": extracted_name,
                "email": extracted_email,
                "phone": extracted_phone,
                "summary": extracted_summary,
                "experience_status": extracted_experience_status,
                "years_of_experience": extracted_years_of_experience,
                "suitable_roles": suitable_roles,
                "path": resume_url,
                "text": text
            })

            uploaded_resumes.append({
                "id": str(resume_id),
                "name": extracted_name,
                "email": extracted_email,
                "message": "Resume uploaded successfully!"
            })

        except Exception as e:
            logger.error(f"Error processing {file.filename}: {e}")

    if not uploaded_resumes:
        return JSONResponse(status_code=400, content={"error": "No valid resumes uploaded"})

    return uploaded_resumes[0] if len(uploaded_resumes) == 1 else {"uploaded_resumes": uploaded_resumes}


# Retrieve All Resumes from Database
@resume.get("/get-all")
async def get_all_resumes():
    """
    Fetches all resumes stored in the database.
    Returns a list of resume records.
    """
    return db.get_all("resumes")


@resume.delete("/delete/{resume_id}")
async def delete_resume(resume_id: str):
    """
    Deletes a resume from the database and its corresponding blob in Azure Storage.
    """
    # Fetch Resume Details
    resume_data = db.get("resumes", resume_id)
    if not resume_data:
        raise HTTPException(status_code=404, detail="Resume not found")

    resume_url = resume_data["path"]
    
    blob_name = urlparse(resume_url).path.split("/")[-1]
    decoded_blob_name = unquote(blob_name)

    # Delete Resume from DB
    deleted = db.delete("resumes", resume_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete resume from database")

    # Delete Blob from Azure
    result = await delete_blob(RESUME_CONTAINER_NAME, decoded_blob_name)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return {"message": f"Resume '{resume_id}' and blob deleted successfully!"}