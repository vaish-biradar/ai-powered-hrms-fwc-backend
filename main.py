from fastapi import FastAPI,Depends
from fastapi.middleware.cors import CORSMiddleware
import os

try:
    import certifi
    if not os.environ.get("SSL_CERT_FILE"):
        os.environ["SSL_CERT_FILE"] = certifi.where()
    if not os.environ.get("REQUESTS_CA_BUNDLE"):
        os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
except ImportError:
    pass

# Utility functions
from routers.match import match
from routers.jd import jd
from routers.resume import resume
from routers.analysis import analysis
from routers.cleardb import cleardb
from routers.sendemail import sendemail
from routers.agent import dohragent
from routers.transcript import transcript_analysis
from routers.hrms import hrms
from utils.security import verify_api_key
# Initialize FastAPI app
app = FastAPI()

# Allow CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://www.fwc.co.in","https://jolly-stone-04f2ae30f.6.azurestaticapps.net","http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Server is up and running 🚀"}

# Include routers
app.include_router(match, dependencies=[Depends(verify_api_key)])
app.include_router(jd, dependencies=[Depends(verify_api_key)])
app.include_router(resume, dependencies=[Depends(verify_api_key)])
app.include_router(analysis)
app.include_router(cleardb, dependencies=[Depends(verify_api_key)])
app.include_router(sendemail, dependencies=[Depends(verify_api_key)])
app.include_router(dohragent, dependencies=[Depends(verify_api_key)])
app.include_router(transcript_analysis, dependencies=[Depends(verify_api_key)])
app.include_router(hrms, dependencies=[Depends(verify_api_key)])