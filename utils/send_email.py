import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
# Load environment variables
load_dotenv()
from urllib.parse import urlparse,unquote
# SMTP Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
GMAIL_USERNAME = os.getenv("GMAIL_USERNAME")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")
RESUME_CONTAINER_NAME=os.getenv("RESUME_CONTAINER_NAME")
from utils.file_utils import download_blob_to_bytes
from utils.logger_config import logger  # Logging configuration
def send_email(candidate_email: str, candidate_name: str, job_title: str, job_description: str):
    """
    Sends a simple job opportunity email to the candidate.

    Args:
        candidate_email (str): Recipient's email.
        candidate_name (str): Candidate's name.
        job_title (str): Job title.
        job_description (str): Description of the job.

    Returns:
        bool: True if email is sent successfully, False otherwise.
    """
    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL_USERNAME
        msg['To'] = candidate_email
        msg['Subject'] = f"Job Opportunity at FWC India Pvt Ltd: {job_title}"

        # Simple Email Body
        email_body = f"""
        <p>Hi {candidate_name},</p>
        <p>We have reviewed your profile and found a potential match for the following role at <strong>FWC India Pvt Ltd</strong>:</p>
        <p><strong>{job_title}</strong></p>
        <p>{job_description}</p>
        <p>Would you be interested in applying for this role? Let us know your availability.</p>
        <p>Best Regards,<br>
        HR Team<br>
        FWC India Pvt Ltd<br>
        <a href="https://www.fwc.co.in">www.fwc.co.in</a></p>
        """

        msg.attach(MIMEText(email_body, 'html'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(GMAIL_USERNAME, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USERNAME, candidate_email, msg.as_string())

        print("✅ Email sent successfully!")
        return True

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False


 
async def send_email_with_resume(
    hr_emails: list, candidate_email: str, candidate_name: str, 
    job_title: str, job_description: str, resume_path: str,roles:list, report_url: str
):
    logger.error(roles)
    """Sends an email to HR with the attached resume and AI-generated report."""
    
    # Create the Email
    msg = MIMEMultipart()
    msg["Subject"] = f"Job Application: {candidate_name} for {job_title}"
    msg["From"] = GMAIL_USERNAME
    msg["To"] = ", ".join(hr_emails) 

    # Extract blob names from URLs
    resume_blob_name = unquote(urlparse(resume_path).path.split("/")[-1])
    report_blob_name = unquote(urlparse(report_url).path.split("/")[-1])

    logger.info(f"Resume Blob Name: {resume_blob_name}")
    logger.info(f"Report Blob Name: {report_blob_name}")
    roles_list_html = "".join(f"<li>{role}</li>" for role in roles)
    # Email Body (HTML Format)
    body = f"""
    <html>
    <body>
        <p>Dear HR,</p>
        <p>We have received a new job application for the <b>{job_title}</b> role.</p>
        <p><b>Candidate Name:</b> {candidate_name} ({candidate_email})<br>
        <p><b>Job Description:</b><br>{job_description}</p>
        <p><b>Relevant Roles:</b></p>
        <ul>{roles_list_html}</ul>
        <p>The candidate's resume and AI-generated Analysis report are attached for your reference.</p>
    </body>
    </html>
    """
    msg.attach(MIMEText(body, "html"))

    # Function to attach a file from Azure Blob Storage
    async def attach_file(container_name: str, blob_name: str, filename: str):
        try:
            file_bytes = await download_blob_to_bytes(container_name, blob_name)
            part = MIMEBase("application", "octet-stream")
            part.set_payload(file_bytes)
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={filename}")
            msg.attach(part)
            logger.info(f"Attached file: {filename}")
        except Exception as e:
            logger.error(f"Error downloading {filename} from Blob Storage: {e}")
            raise FileNotFoundError(f"Error downloading {filename} from Blob Storage: {e}")

    # Attach Resume
    await attach_file(RESUME_CONTAINER_NAME, resume_blob_name, resume_blob_name)
    
    # Attach AI-Generated Report
    await attach_file("reports", report_blob_name, report_blob_name)

    # Send Email via Gmail SMTP
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Secure the connection
            server.login(GMAIL_USERNAME, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USERNAME, hr_emails, msg.as_string())

        return "Email sent successfully!"
    
    except smtplib.SMTPAuthenticationError:
        raise smtplib.SMTPAuthenticationError(535, "Authentication failed. Check email credentials.")
    
    except smtplib.SMTPException as e:
        raise smtplib.SMTPException(f"SMTP error occurred: {e}")
    
    except Exception as e:
        raise Exception(f"Unexpected error while sending email: {e}")
