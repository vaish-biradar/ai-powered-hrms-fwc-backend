# FastAPI Project

This project consists of a **FastAPI backend**. Follow the steps below to set up and run the application efficiently.

---

## 📌 Prerequisites
- Python **3.8+** installed
- Virtual environment support (`venv` or `virtualenv`)
- `pip` installed and updated (`pip install --upgrade pip`)

---

## 🚀 Setup Instructions

### 1️⃣ Create a Virtual Environment
Run the following command to create a virtual environment:
```sh
python -m venv myenv
```

### 2️⃣ Activate the Virtual Environment
- **Windows (Command Prompt):**
  ```sh
  myenv\Scripts\activate
  ```
- **Windows (PowerShell):**
  ```sh
  myenv\Scripts\activate.ps1
  ```
- **Mac/Linux:**
  ```sh
  source myenv/bin/activate
  ```

### 3️⃣ Install Dependencies
Install all required Python packages:
```sh
pip install -r requirements.txt
```

### 4️⃣ Set Up Environment Variables
- Create a `.env` file in the root directory.
- Copy the variables from `.env.example` and update them with actual values.

Example:
```sh
cp .env.example .env
```
Then open `.env` and modify the values as needed.

---

## 📂 Project Structure
To maintain a well-organized codebase, follow the recommended folder hierarchy:

```
.
├── opeanaiservice
│   ├── openaiclient.py  # Azure OpenAI Configuration
├── prompts
│   ├── candidate_resume_analysis.py  # Analyzes candidate score compared to JD
│   ├── hr_detailed_resume_analysis.py # Compares candidate resumes
│   ├── job_details_prompt.py # Extracts job title and summary
│   ├── match_jd_to_resume.py # Scores JD against resumes
│   ├── match_resume_to_jds.py # Scores resume against JDs
│   ├── name_email_extraction.py # Extracts name, email, roles, and experience details
├── routers
│   ├── analysis.py  # Endpoints:
│   │   ├── `<url>/candidate` - Candidate analysis report
│   │   ├── `<url>/hr` - HR analysis report
│   ├── cleardb.py  # Endpoint: `<url>/clear-db` - Clears the database
│   ├── jd.py  # Job Description Endpoints:
│   │   ├── `<url>/create`
│   │   ├── `<url>/update/{jd_id}`
│   │   ├── `<url>/get-all`
│   │   ├── `<url>/get/{jd_id}`
│   │   ├── `<url>/delete/{jd_id}`
│   ├── resume.py  # Resume Endpoints:
│   │   ├── `<url>/upload-resume`
│   │   ├── `<url>/get-all`
│   │   ├── `<url>/delete/{resume_id}`
│   ├── match.py  # Matching Endpoints:
│   │   ├── `<url>/resume-to-jds`
│   │   ├── `<url>/jd-to-resumes`
│   ├── sendemail.py  # Email Endpoints:
│   │   ├── `<url>/contact-candidate`
│   │   ├── `<url>/apply-job`
├── assets
│   ├── logos
│   │   ├── logo.png
├── schemas
│   ├── models.py  # Database models and schemas
├── services
│   ├── database.py  # Database operations
│   ├── file_utils.py  # Blob operations & text extraction (PDF, DOCX)
│   ├── logger_config.py  # Logging setup
│   ├── send_email.py  # Email configuration
├── main.py  # Main entry point for FastAPI
├── .env  # Environment variables
├── requirements.txt  # Python dependencies
```

---

## ▶️ Running the Backend (FastAPI)
To start the FastAPI server, run:
```sh
python -m uvicorn main:app --host 127.0.0.1 --port 8012 --reload
```

The API will be available at: [http://127.0.0.1:8012/docs](http://127.0.0.1:8012/docs) 🚀

---

## 🧱 Database Migrations (Alembic)

This backend now uses Alembic for schema versioning.

### Fresh Database Setup
```sh
alembic upgrade head
```

### Existing Database (already has tables)
Use this once to mark the current schema as baseline without re-creating tables:
```sh
alembic stamp head
```

### Create a New Migration
```sh
alembic revision --autogenerate -m "describe_change"
```

### Apply New Migrations
```sh
alembic upgrade head
```

---

## 🔹 Additional Notes
- **Deactivate the virtual environment:**
  ```sh
  deactivate
  ```
- **Install additional packages:**
  ```sh
  pip install <package-name>
  ```
  Then update `requirements.txt`:
  ```sh
  pip freeze > requirements.txt
  ```

Happy coding! 🎉

