from pydantic import BaseModel
from typing import List
class MatchRequest(BaseModel):
    resume_id: str

class JDMatchRequest(BaseModel):
    jd_id: str
    apply_filter: bool

class EmailRequest(BaseModel):
    candidate_email: str
    candidate_name: str
    job_title: str
    job_description: str

class FormData(BaseModel):
    name: str
    email: str
    mobile: str
    totalExperience: str
    currentCtc: str
    expectedCtc: str
    currentCompany: str
    currentLocation: str
    currentJobTitle: str
    noticePeriod: str

# Update ApplyRequest model to include FormData
class ApplyRequest(BaseModel):
    resume_id: str
    jd_id: str
    similarity: float
    formdata: FormData
    source:str
class CompareRequest(BaseModel):
    jd_id: str
    candidates: List[str]
    
class CancelRequest(BaseModel):
    file_path: str


class MockInterviewMessage(BaseModel):
    role: str
    content: str


class MockInterviewChatRequest(BaseModel):
    resume_id: str
    jd_id: str
    messages: List[MockInterviewMessage]


class MockInterviewSaveRequest(BaseModel):
    resume_id: str
    jd_id: str
    candidate_name: str
    candidate_email: str
    conversation: List[MockInterviewMessage]


class TranscriptTextRequest(BaseModel):
    transcript_text: str