import os
import pymupdf  # PyMuPDF
import io
from fastapi import UploadFile
from urllib.parse import urlparse,unquote
from dotenv import load_dotenv
from azure.storage.blob.aio import BlobServiceClient
from utils.logger_config import logger  # Logging configuration
from azure.storage.blob import  generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta,timezone
import zipfile
import xml.etree.ElementTree as ET
load_dotenv()
CONNECTION_STRING = os.getenv("STORAGE_ACCOUNT_CONNECTION_STRING")
STORAGE_ACCOUNT_KEY=os.getenv("STORAGE_ACCOUNT_KEY")

from datetime import datetime
import os

async def save_file(file: UploadFile, container_name: str) -> str:
    """Save uploaded file to Azure Blob Storage asynchronously and return its URL with date-appended filename."""

    # ⏱️ Add current date to the filename
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    name, ext = os.path.splitext(file.filename)
    dated_filename = f"{name}_{date_str}{ext}"

    logger.info(f"Preparing to save file: {dated_filename} to container: {container_name}")

    async with BlobServiceClient.from_connection_string(CONNECTION_STRING) as blob_service_client:
        container_client = blob_service_client.get_container_client(container_name)

        # ✅ Ensure container exists
        try:
            await container_client.get_container_properties()
            logger.info(f"Container '{container_name}' exists.")
        except Exception as e:
            await container_client.create_container()
            logger.info(f"Container '{container_name}' created.")

        blob_client = container_client.get_blob_client(dated_filename)

        # 📤 Upload directly to Azure
        file_data = await file.read()
        await blob_client.upload_blob(file_data, overwrite=True)

        logger.info(f"File '{dated_filename}' uploaded successfully to Azure Blob Storage.")
        return blob_client.url



async def download_blob_to_bytes(container_name: str, blob_name: str) -> bytes:
    """Download a blob from Azure Storage as bytes."""
    async with BlobServiceClient.from_connection_string(CONNECTION_STRING) as blob_service_client:
        blob_client = blob_service_client.get_blob_client(container_name, blob_name)
        try:
            stream = await blob_client.download_blob()
            return await stream.readall()
        finally:
            await blob_service_client.close()  # Ensure client is closed


async def extract_text_from_txt(blob_data: bytes) -> str:
    """Extract text from a TXT file."""
    return blob_data.decode("utf-8").strip()


async def extract_text_from_pdf(blob_data: bytes) -> str:
    """Extract text from a PDF file."""
    text = ""
    with pymupdf.open(stream=io.BytesIO(blob_data)) as doc:
        for page in doc:
            text += page.get_text("text") + "\n"
    return text.strip()


async def extract_text_from_docx(blob_data: bytes) -> str:
    """Extracts all text from a DOCX file, including paragraphs, tables, headers, footnotes, textboxes, comments, and metadata."""
    
    text_content = []
    
    # Load DOCX as a zip archive (DOCX is a ZIP file)
    with zipfile.ZipFile(io.BytesIO(blob_data), "r") as docx_zip:
        # Extract text from document body
        if "word/document.xml" in docx_zip.namelist():
            text_content.append(parse_xml_text(docx_zip.read("word/document.xml")))

        # Extract headers & footers
        for part in docx_zip.namelist():
            if part.startswith("word/header"):
                text_content.append("Header: " + parse_xml_text(docx_zip.read(part)))
            elif part.startswith("word/footer"):
                text_content.append("Footer: " + parse_xml_text(docx_zip.read(part)))

        # Extract footnotes & endnotes
        if "word/footnotes.xml" in docx_zip.namelist():
            text_content.append("Footnotes: " + parse_xml_text(docx_zip.read("word/footnotes.xml")))
        if "word/endnotes.xml" in docx_zip.namelist():
            text_content.append("Endnotes: " + parse_xml_text(docx_zip.read("word/endnotes.xml")))

        # Extract comments (Review comments in DOCX)
        if "word/comments.xml" in docx_zip.namelist():
            text_content.append("Comments: " + parse_xml_text(docx_zip.read("word/comments.xml")))

        # Extract custom fields & metadata
        if "docProps/core.xml" in docx_zip.namelist():
            text_content.append("Metadata: " + parse_xml_text(docx_zip.read("docProps/core.xml")))

    return "\n".join([t for t in text_content if t]).strip()

def parse_xml_text(xml_data: bytes) -> str:
    """Parses XML data and extracts text content."""
    root = ET.fromstring(xml_data)
    return " ".join(node.text.strip() for node in root.iter() if node.text)


async def extract_text_from_file(container_name: str, blob_url: str) -> str:
    """Extract text from a file in Azure Blob Storage based on its format (TXT, PDF, DOCX)."""
    # Extract blob name from the URL
    blob_name = urlparse(blob_url).path.split("/")[-1]
    logger.info("blob_name: %s", blob_name)
    decoded_blob_name = unquote(blob_name)
    logger.info("decoded_blob_name: %s", decoded_blob_name)
    blob_data = await download_blob_to_bytes(container_name, decoded_blob_name)
    
    if blob_name.endswith(".txt"):
        return await extract_text_from_txt(blob_data)
    elif blob_name.endswith(".pdf"):
        return await extract_text_from_pdf(blob_data)
    elif blob_name.endswith(".docx"):
        return await extract_text_from_docx(blob_data)
    else:
        return None  # Return None for unsupported file formats



async def delete_blob(container_name: str, blob_name: str):
    """
    Deletes a blob from Azure Blob Storage asynchronously.

    :param container_name: The name of the Azure Blob Storage container.
    :param blob_name: The name (path) of the blob inside the container.
    :return: A success message or an error.
    """
    try:
        async with BlobServiceClient.from_connection_string(CONNECTION_STRING) as blob_service_client:
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

            # Delete the blob
            await blob_client.delete_blob()

            return {"message": f"Blob '{blob_name}' deleted successfully from container '{container_name}'"}
    except Exception as e:
        return {"error": f"Failed to delete blob: {str(e)}"}
    
    
async def generate_sas_url(blob_url,container_name):
    
    blob_name = urlparse(blob_url).path.split("/")[-1]
    logger.info("blob_name: %s", blob_name)
    decoded_blob_name = unquote(blob_name)
    
    blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=decoded_blob_name)

    sas_token = generate_blob_sas(
        account_name=blob_service_client.account_name,
        container_name=container_name,
        blob_name=decoded_blob_name,
        account_key=STORAGE_ACCOUNT_KEY,
        permission=BlobSasPermissions(read=True),
        expiry = datetime.now(timezone.utc) + timedelta(hours=1)  # Valid for 1 hour
    )

    return f"{blob_client.url}?{sas_token}"    