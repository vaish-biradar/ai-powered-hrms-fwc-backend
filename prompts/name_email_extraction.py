
def get_name_email_extraction_prompt(resume_text: str) -> list:
    """
    Generates the LLM prompt for extracting a candidate's name, email, experience status with years, and suitable roles from a resume.
    """
    return [
        {
            "role": "system",
            "content": "You are an AI assistant specialized in resume analysis. Your task is to extract structured details from a resume."
        },
        {
            "role": "user",
            "content": f"""
                Extract the following details from the given resume:

                1. Candidate's full name
                2. Email address
                3. Phone number (if country code dont exists then add +91 or related country code to that number and give all number in format of +`country code` `number`)
                4. List of potential roles the candidate can fit into (based on skills and experience)
                5. A summary of the candidate, including their key skills, qualifications, and any notable achievements
                6. Whether the candidate has mentioned work experience; if not, classify them as 'Fresher'
                7. If experienced, extract the number of years of experience mentioned. If no experience is mentioned, return "0 years".

                Resume:
                {resume_text}

                Return the result **only** in this JSON format, without any extra text:
                {{
                    "name": "Candidate Name",
                    "email": "candidate@example.com",
                    "phone": "+`country code` `number`",
                    "suitable_roles": ["Role 1", "Role 2", "Role 3"],
                    "summary": "Detailed summary including key skills, qualifications, and any notable achievements.",
                    "experience_status": "Experienced" or "Fresher",
                    "years_of_experience": "X years" or "0 years"
                }}
            """
        }
    ]
