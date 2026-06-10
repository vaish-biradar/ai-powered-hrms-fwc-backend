import os
import json
from fastapi import HTTPException, APIRouter
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import AzureOpenAI
from sqlmodel import Session, select
from typing import Optional, List, Dict, Any
from utils.logger_config import logger  # Logging configuration

# Import the PostgreSQL models and connection
from utils.database import  JobDescription, Application, db

load_dotenv()

dohragent = APIRouter(prefix="/dohragent", tags=["hragent"])

# Azure OpenAI Setup
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")


# Initialize Azure OpenAI client
from openaiservice.openaiclient import client  # OpenAI client for LLM interaction


def get_application_status(email: str) -> str:
    """Retrieves the application status from PostgreSQL DB based on the user's email, handling multiple applications."""
    try:
        logger.info(f"Fetching application status for email: {email}")
        
        with Session(db.engine) as session:
            # Query applications by candidate email
            statement = select(Application).where(Application.candidate_email == email)
            results = session.exec(statement).all()
            
            if not results:
                logger.warning(f"No application found for email: {email}")
                return f"No application found for email: {email}"
            
            # Formatting the response for multiple applications
            response_lines = []
            for application in results:
                job_title = application.job_title or "Unknown Job Title"
                status = application.status or "Unknown Status"
                candidate_name = application.candidate_name or "Unknown Candidate"
                response_lines.append(f"Candidate: {candidate_name}, Job Title: {job_title}, Status: {status}")
            
            return "\n".join(response_lines)
    
    except Exception as e:
        logger.error(f"Error retrieving application status for {email}: {str(e)}")
        return f"Error retrieving application status: {str(e)}"


def get_job_descriptions(title: str = None, fetch_all: bool = False, fetch_skills: bool = False) -> str:
    """Fetches job descriptions from PostgreSQL DB with strict title matching, providing suggestions if not found."""
    try:
        with Session(db.engine) as session:
            if fetch_all:
                logger.info("Fetching all open job descriptions")
                statement = select(JobDescription).where(JobDescription.status == "Open")
                results = session.exec(statement).all()
                
                if not results:
                    return "No open job descriptions found."
                
                return "\n".join([f"{job.title} - {job.department} ({job.location})" for job in results])
            
            elif title:
                logger.info(f"Fetching job details for title: {title}")
                statement = select(JobDescription).where(JobDescription.title == title)
                job = session.exec(statement).first()
                
                if not job:
                    # Fetch all open job titles to suggest
                    statement = select(JobDescription.title).where(JobDescription.status == "Open")
                    all_jobs = session.exec(statement).all()
                    
                    if not all_jobs:
                        return "No open job descriptions found."
                    
                    available_titles = [job_title for job_title in all_jobs]
                    available_titles_str = ", ".join(available_titles)
                    return f"No job found with title '{title}'. Available titles are: {available_titles_str}. Please specify the exact title."
                
                if fetch_skills:
                    return f"Required skills for {title}: {job.skills}"
                else:
                    # Construct job details with experience handling
                    experience_level = job.experience_level.strip() if job.experience_level else ''
                    experience_line = f"Experience: {experience_level}" if experience_level else "Experience information is not available."
                    job_details = f"""
                    **{job.title}**
                    Department: {job.department or 'N/A'}
                    Location: {job.location or 'N/A'}
                    {experience_line}
                    Summary: {job.summary or 'N/A'}
                    Skills: {job.skills or 'N/A'}
                    Job Details: {job.path or 'N/A'}
                    """
                    return job_details.strip()
            
            elif fetch_skills:
                # fetch_skills is True but no title provided
                return "Please provide a job title to fetch the required skills."
            
            else:
                return "Please specify a job title or set 'fetch_all' to True to list all open jobs."
    
    except Exception as e:
        logger.error(f"Error fetching job details: {str(e)}")
        return f"Error fetching job details: {str(e)}"


class UserInput(BaseModel):
    prompt: str


@dohragent.post("/agent")
async def agent_response(user_input: UserInput):
    try:
        logger.info(f"Received user prompt: {user_input.prompt}")
        
        company_info = """
        # FWC India Pvt Ltd

        ## Website Navigation
        - Home
        - Who we serve
        - What we do
        - Who we are
        - Why Choose Us
        - Career at FWC
        - Contact Us

        ## Home
        **We Engineer Your Success for the Digital Future**

        Build, protect, and grow your business through expert consulting and technology solutions designed to advance every industry.

        ### Delivery Highlights
        - 57+ Projects Delivered
        - 20+ Global Clients
        - 10+ Service Excellence
        - 83+ Niche Skills
        - 4.8/5 from 3,602 customers

        ## Mission
        Our mission is to empower businesses by delivering agile staffing, expert consulting, and scalable project outsourcing for growth and innovation.

        ## What We Do (Services)
        - AI and Advanced Technology
        - Technology and Product Development
        - Cloud and Infrastructure Services
        - Recruitment Process Outsourcing
        - Cybersecurity
        - IT Managed Services
        - IT Contingent Staffing
        - Blockchain
        - Consulting

        ## Service Pillars
        - Technology and Product Services
        - Cloud and Infrastructure Services
        - AI and Advanced Technologies
        - Talent and Workforce Solutions

        ## Who We Serve (Industries)
        - Fintech
        - Manufacturing
        - Telecommunications
        - Healthcare
        - Retail and E-commerce
        - Banking and Finance
        - Education Technology
        - Media and Gaming

        ## Why Choose Us
        FWC focuses on fast execution, high-quality talent delivery, and business continuity support across critical and niche technology roles.

        ## Career at FWC
        Candidates can explore open opportunities and apply through the careers portal.

        ## Contact
        - US: #2112 Chestnut St, Suite 109, Alhambra, California, US 91803
        - India: #1348 7th Avenue, 2nd and 4th Floor, Jayanagar 9th Block, Bangalore, Karnataka, India 560011

        ## Website Details
        - Website: https://www.fwc.co.in
        - Careers: https://www.fwc.co.in/careers
        """

        
        
        system_message = {
            "role": "system",
            "content": f"""
You are a job search assistant for FWC India Pvt Ltd. Follow these rules strictly:

1. Application status checks:
- Always require the user's email address before checking status.

2. Job details:
- Verify exact job title before sharing details.
- If title not found, show available open positions.

3. No fabrication:
- Use only real job listings from database.
- Never invent roles, skills, or status.

4. Skills and experience:
- Confirm exact job title first, then provide skills/experience.

5. Response style:
- Keep answers concise and structured.
- Use Markdown format for frontend rendering.

6. How to apply:
- Guide user to careers page: https://www.fwc.co.in/careers
- Mention resume upload and match-based application flow.

7. Company information policy:
- Use only the company_info below.
- Give short summaries tied to the user's question.
- Do not dump full company_info unless explicitly asked.
- For unrelated company questions: "Please visit our website: https://www.fwc.co.in"

8. Task identity:
- If asked what you do, reply: "I am FWC Assistant here to help you with company details, job searches, and application status."

9. Restricted topics:
- No general knowledge help.
- No non-FWC job searches.
- No political, personal, or financial advice.
- No code generation/debugging.

10. Violation response:
- "I only assist with FWC job searches and company details. Please ask relevant questions."

company_info:
{company_info}
""",
        }

        
        messages = [system_message, {"role": "user", "content": user_input.prompt}]

        functions = [
    {
                "name": "get_application_status",
                "description": "Retrieves the application status from Cosmos DB based on the user's email. Make response clear and structured way. if not found application tell directly . and its still in applied state tell like we will get back to you",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "email": {"type": "string", "description": "The user's email address."}
                    },
                    "required": ["email"],
                },
            },
    {
        "name": "get_job_descriptions",
        "description": (
            "Access job listings database. Always verify exact title match first. "
            "If title not found, list available open positions. "
            "For skills/experience queries, confirm exact title before providing details."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string", 
                    "description": "Exact job title to lookup. Must match database entry exactly. Confirm with user if uncertain."
                },
                "fetch_all": {
                    "type": "boolean",
                    "description": "True to list all open positions. Use when user asks 'list all jobs' or similar.",
                    "default": False
                },
                "fetch_skills": {
                    "type": "boolean",
                    "description": "True to get skills for SPECIFIC job. Requires exact title first.",
                    "default": False
                },
            },
        },
    }
]
        
        # Convert functions to tools format for newer models
        tools = [{"type": "function", "function": func} for func in functions]
        
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=messages,
            tools=tools,
        )
        response_message = response.choices[0].message

        if hasattr(response_message, "tool_calls") and response_message.tool_calls:
            tool_call = response_message.tool_calls[0]
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            logger.info(f"Function args: {function_args}")

            if function_name == "get_application_status":
                status_result = get_application_status(function_args["email"])
            elif function_name == "get_job_descriptions":
                status_result = get_job_descriptions(**function_args)

            messages.append(response_message)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": status_result
            })

            second_response = client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=messages,
            )
            return {"response": second_response.choices[0].message.content}

        return {"response": response_message.content}

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

