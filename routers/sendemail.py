from fastapi import APIRouter, HTTPException, BackgroundTasks
import os
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListItem, ListFlowable
from reportlab.lib.units import inch
import io
# Utility functions
from utils.send_email import send_email, send_email_with_resume  # Email utility functions
from utils.logger_config import logger  # Logging configuration
from schemas.models import EmailRequest, ApplyRequest  # Request models
from prompts.hr_detailed_resume_report import get_detailed_resume_report_prompt  # Detailed report prompt
from openaiservice.openaiclient import client  # OpenAI client initialization
import asyncio
from azure.storage.blob.aio import BlobServiceClient
from azure.storage.blob import ContentSettings
import markdown
from bs4 import BeautifulSoup
import re
import uuid
# Load environment variables
load_dotenv()


raw_emails = os.getenv("HR_EMAIL")
HR_EMAILS1 = os.getenv("HR_EMAILS")


HR_EMAILS = HR_EMAILS1.split(",") if HR_EMAILS1 else []

AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
CONNECTION_STRING = os.getenv("STORAGE_ACCOUNT_CONNECTION_STRING")
# Initialize database from main file
from utils.database import db  # Directly import db
from datetime import datetime,timezone# Utility functions



# Create FastAPI router for email-related endpoints
sendemail = APIRouter(prefix="/sendemail", tags=["sendemail"])


@sendemail.post("/contact-candidate")
def send_candidate_email(email_request: EmailRequest, background_tasks: BackgroundTasks):
    """ Sends an email to a candidate asynchronously. """
    try:
        # Add email task to background queue for async processing
        background_tasks.add_task(
            send_email,
            email_request.candidate_email,
            email_request.candidate_name,
            email_request.job_title,
            email_request.job_description,
        )
        return {"message": "Email sent successfully"}
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending email: {str(e)}")




def parse_markdown_tables(md_text):
    """
    Parse markdown tables into data that can be used by ReportLab
    Improved version that handles complex table structures better
    """
    table_data = []
    lines = md_text.split('\n')
    current_table = []
    in_table = False
    
    for line in lines:
        # Check if line is part of a table (starts and ends with |)
        stripped_line = line.strip()
        if stripped_line and stripped_line.startswith('|') and stripped_line.endswith('|'):
            if not in_table:
                in_table = True
                current_table = []
            
            # Skip separator lines (those with only dashes, colons, and pipes)
            if re.match(r'\|\s*[-:\s|]+\s*\|$', stripped_line):
                continue
                
            # Process row: split by |, remove first and last empty elements, and strip whitespace
            cells = [cell.strip() for cell in stripped_line.split('|')[1:-1]]
            current_table.append(cells)
        elif in_table:
            # We've reached the end of a table
            in_table = False
            if current_table:
                table_data.append(current_table)
                current_table = []
    
    # Add the last table if we ended while still in one
    if in_table and current_table:
        table_data.append(current_table)
    
    return table_data

def create_reportlab_tables(table_data):
    """
    Convert parsed table data into ReportLab Table objects with improved styling
    and special character handling
    """
    tables = []
    
    # Map unicode symbols to ReportLab-friendly symbols
    symbol_mapping = {
        '✓': 'Yes',  # ReportLab checkmark
        '✔': 'Yes', 
        '✅': 'Yes',
        '❌': 'No',  # ReportLab X mark
        '■': 'Yes',
        '❏': 'No',
        '–': '-',
        '—': '-',
        '-': '-'
    }
    
    for data in table_data:
        if not data or len(data) < 2:  # Need at least header row and one data row
            continue
        
        # Replace special characters with ReportLab-friendly versions
        processed_data = []
        for row in data:
            processed_row = []
            for cell in row:
                # Replace special characters
                for symbol, replacement in symbol_mapping.items():
                    cell = cell.replace(symbol, replacement)
                processed_row.append(cell)
            processed_data.append(processed_row)
            
        # Create the table with first row as header
        table = Table(processed_data, repeatRows=1)
        
        # Apply better styling
        style = [
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            
            # Cell borders
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            
            # Text alignment - center header, left-align data
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            
            # Padding for all cells
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ]
        
        # Add zebra striping for readability
        for i in range(1, len(processed_data), 2):
            style.append(('BACKGROUND', (0, i), (-1, i), colors.whitesmoke))
        
        table.setStyle(TableStyle(style))
        tables.append(table)
    
    return tables

def extract_tables_from_markdown(md_text):
    """
    Extracts tables from markdown text and returns both the tables and the text with tables removed
    """
    # Find all table sections in the markdown text
    lines = md_text.split('\n')
    table_sections = []
    non_table_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Check if this line starts a table
        if line and line.startswith('|') and line.endswith('|'):
            # Found start of a table
            table_start = i
            table_lines = [lines[i]]
            i += 1
            
            # Collect all lines that are part of this table
            while i < len(lines) and lines[i].strip() and lines[i].strip().startswith('|') and lines[i].strip().endswith('|'):
                table_lines.append(lines[i])
                i += 1
            
            # Extract the table section
            table_sections.append('\n'.join(table_lines))
            
            # Mark where we should insert the table in the non-table content
            non_table_lines.append(f"[TABLE_{len(table_sections) - 1}]")
        else:
            non_table_lines.append(lines[i])
            i += 1
    
    remaining_text = '\n'.join(non_table_lines)
    return table_sections, remaining_text

def markdown_to_reportlab(md_text):
    """
    Convert markdown text to a list of ReportLab flowables with better table handling
    """
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'Title', 
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=12
    )
    
    heading1_style = ParagraphStyle(
        'Heading1', 
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=10
    )
    
    heading2_style = ParagraphStyle(
        'Heading2', 
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=8
    )
    
    normal_style = ParagraphStyle(
        'Normal', 
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )
    
    # Extract tables first and replace them with placeholders
    table_sections, text_without_tables = extract_tables_from_markdown(md_text)
    
    # Parse the remaining markdown to HTML
    html = markdown.markdown(text_without_tables)
    soup = BeautifulSoup(html, 'html.parser')
    
    flowables = []
    
    # Process each HTML element
    for element in soup.find_all(['h1', 'h2', 'h3', 'p', 'ul', 'ol']):
        if element.name == 'h1':
            flowables.append(Paragraph(element.text, title_style))
        elif element.name == 'h2':
            flowables.append(Paragraph(element.text, heading1_style))
        elif element.name == 'h3':
            flowables.append(Paragraph(element.text, heading2_style))
        elif element.name == 'p':
            text = element.text
            
            # Look for table placeholders and insert tables
            if '[TABLE_' in text:
                for i, table_marker in enumerate(re.findall(r'\[TABLE_(\d+)\]', text)):
                    table_idx = int(table_marker)
                    
                    # Split text at table marker
                    parts = text.split(f"[TABLE_{table_idx}]", 1)
                    
                    # Add text before table
                    if parts[0].strip():
                        flowables.append(Paragraph(parts[0].strip(), normal_style))
                    
                    # Process and add the table
                    table_md = table_sections[table_idx]
                    table_data = parse_markdown_tables(table_md)
                    if table_data:
                        tables = create_reportlab_tables(table_data)
                        for table in tables:
                            flowables.append(table)
                            flowables.append(Spacer(1, 0.2*inch))
                    
                    # Update text to remaining portion
                    text = parts[1] if len(parts) > 1 else ""
                
                # Add any remaining text
                if text.strip():
                    flowables.append(Paragraph(text.strip(), normal_style))
            else:
                flowables.append(Paragraph(text, normal_style))
                
        elif element.name in ['ul', 'ol']:
            try:
                items = []
                for li in element.find_all('li'):
                    items.append(ListItem(Paragraph(li.text, normal_style)))
                
                # Fix: use '1' instead of 'numbered' for ordered lists
                list_style = 'bullet' if element.name == 'ul' else '1'
                flowables.append(ListFlowable(items, bulletType=list_style))
                flowables.append(Spacer(1, 0.1*inch))
            except Exception as e:
                # Fallback: convert list to paragraphs
                for li in element.find_all('li'):
                    prefix = "• " if element.name == 'ul' else f"{element.find_all('li').index(li) + 1}. "
                    flowables.append(Paragraph(f"{prefix}{li.text}", normal_style))
                flowables.append(Spacer(1, 0.1*inch))
    
    # Process any tables that weren't already inserted
    for table_section in table_sections:
        # Check if this table was already processed through a placeholder
        if f"[TABLE_{table_sections.index(table_section)}]" not in text_without_tables:
            table_data = parse_markdown_tables(table_section)
            if table_data:
                tables = create_reportlab_tables(table_data)
                for table in tables:
                    flowables.append(table)
                    flowables.append(Spacer(1, 0.2*inch))
    
    return flowables

async def generate_and_upload_report(resume_id: str, jd_id: str):
    """
    Generates AI-driven HR report, saves it as a PDF, uploads it to Azure Blob Storage,
    and returns the shareable URL.
    """
    try:
        logger.info("Generating HR report")
        logger.info(f"{resume_id} {jd_id}")
        # Fetch resume and JD from the database
        resume = db.get("resumes", resume_id)
        jd = db.get("jds", jd_id)

        if not resume or not jd:
            logger.error("Resume or Job Description not found for report generation.")
            return None

        # Prepare messages for AI model
        messages = get_detailed_resume_report_prompt(jd["text"], resume["text"])

        # Call Azure OpenAI API asynchronously
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=messages,
            max_completion_tokens=1000,
            stream=False
        )

        # Extract the AI-generated content
        report_text = response.choices[0].message.content if response.choices else "No content generated."

        # Generate PDF file
          # Create PDF with better formatting
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=36, bottomMargin=36)
        
        styles = getSampleStyleSheet()
        title_style = styles["Title"]
        heading1_style = styles["Heading1"]
        heading2_style = styles["Heading2"]
        normal_style = styles["Normal"]
        
        # Build document content
        content = []
        
        # Title section
        content.append(Paragraph(f"Candidate Analysis Report", title_style))
        content.append(Spacer(1, 0.25*inch))
     
        
        # Convert the markdown report to ReportLab flowables
        flowables = markdown_to_reportlab(report_text)
        content.extend(flowables)
        
        # Build and save PDF
        doc.build(content)
        
        # Reset buffer position
        buffer.seek(0)

        # Upload PDF to Azure Blob Storage
        
        resume_name_clean = re.sub(r"[^\w\s-]", "", resume["name"]).replace(" ", "_")
        job_title_clean = re.sub(r"[^\w\s-]", "", jd["title"]).replace(" ", "_")

        # Construct sanitized filename
        file_name = f"{resume_name_clean}__{job_title_clean}_Report.pdf"

        # Save to Azure Blob Storage
        report_url = await save_file(buffer, file_name, "reports")
        
        logger.info(f"----------------------------------------------------")
        logger.info(f"Report generated and uploaded successfully: {report_url}")
        logger.info(f"----------------------------------------------------")

        return report_url

    except Exception as e:
        logger.error(f"Error generating/uploading report: {e}")
        return None


async def save_file(file_data: io.BytesIO, filename: str, container_name: str) -> str:
    """Save file to Azure Blob Storage asynchronously and return its URL."""
    try:
        async with BlobServiceClient.from_connection_string(CONNECTION_STRING) as blob_service_client:
            container_client = blob_service_client.get_container_client(container_name)

            # Ensure container exists
            try:
                await container_client.get_container_properties()
            except Exception:
                await container_client.create_container()

            blob_client = container_client.get_blob_client(filename)

            # Upload file
            await blob_client.upload_blob(
    file_data.getvalue(),
    overwrite=True,
    content_settings=ContentSettings(content_type="application/pdf")
)

            return blob_client.url  # Return the URL of the uploaded blob

    except Exception as e:
        logger.error(f"Error uploading file to Azure Blob Storage: {e}")
        return None






@sendemail.post("/apply-job")
async def apply_for_job(request: ApplyRequest, background_tasks: BackgroundTasks):
    """Handles job applications by retrieving details from LocalDB and emailing HR."""
    logger.info(f"Received job application request: {request}")

    # ✅ Extract formdata
    formdata = request.formdata
    candidate_name = formdata.name
    candidate_email = formdata.email
    candidate_phone = formdata.mobile
    total_experience = formdata.totalExperience
    current_ctc = formdata.currentCtc
    expected_ctc =formdata.expectedCtc
    current_company = formdata.currentCompany
    current_location = formdata.currentLocation
    current_job_title = formdata.currentJobTitle
    notice_period = formdata.noticePeriod

    logger.info(f"Candidate Details: {candidate_name}, {candidate_email}, {candidate_phone}, {total_experience}, {current_ctc}, {current_location}, {current_job_title}, {notice_period}")

    # ✅ Fetch Resume and Job Details from the database
    resume_data = db.get("resumes", request.resume_id)
    job_data = db.get("jds", request.jd_id)
    source = request.source

    if not resume_data:
        logger.warning(f"Resume with ID {request.resume_id} not found.")
        raise HTTPException(status_code=404, detail="Resume not found")

    if not job_data:
        logger.warning(f"Job with ID {request.jd_id} not found.")
        raise HTTPException(status_code=404, detail="Job details not found")

    # ✅ Check if the candidate has already applied for the same job role
    existing_application = db.find_one(
        "applications",
        {"candidate_email": candidate_email, "job_title": job_data.get("title")}
    )

    if existing_application:
        logger.info(f"Candidate {candidate_email} has already applied for job '{job_data.get('title')}'.")
        return {"message": "You have already applied for this job. We will get back to you soon."}

    # ✅ Generate and upload report
    try:
        report_url = await generate_and_upload_report(request.resume_id, request.jd_id)
        logger.info("----------------------------------------------------")
        logger.info(f"Report URL: {report_url}")
        logger.info("----------------------------------------------------")

    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail="Error generating application report")
    application_id = uuid.uuid4()
    # ✅ Construct application data
    application_data = {
        "id": application_id,
        "resume_id": request.resume_id,
        "job_description_id": request.jd_id,
        "candidate_name": candidate_name,
        "candidate_email": candidate_email,
        "candidate_phone": candidate_phone,
        "total_experience": total_experience,
        "current_ctc": current_ctc,
        "expected_ctc": expected_ctc,
        "current_company": current_company,
        "current_location": current_location,
        "current_job_title": current_job_title,
        "notice_period": notice_period,
        "resume_url": resume_data.get("path"),
        "job_title": job_data.get("title"),
        "jd_url": job_data.get("path"),
        "report_url": report_url,
        "suitable_roles": resume_data.get("suitable_roles", []),
        "applied_date": datetime.now(timezone.utc).isoformat(),
        "similarity": request.similarity,
        "status": "applied",
        "source": source,
    }

    # ✅ Insert into database
    try:
        db.insert("applications", application_data)

        # ✅ Send job application email asynchronously
        background_tasks.add_task(
            send_email_with_resume,
            HR_EMAILS,
            candidate_email,
            candidate_name,
            job_data.get("title"),
            job_data.get("summary"),
            resume_data.get("path"),
            resume_data.get("suitable_roles", []),
            str(report_url),
        )

        logger.info(f"Application successfully submitted for {candidate_name}")
        return {"message": "Application submitted successfully!"}

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

