def get_match_jd_to_resumes(jd_text: str, resume_text: str) -> list:
    """
    Generates a structured prompt for evaluating a job description against a resume
    based on five weighted criteria:

    1. Role Alignment (40%)
    2. Skills Match (30%)
    3. Experience Match (20%)
    4. Education Match (5%)
    5. Certification Match (5%)

    The output should be a single weighted relevance score between 0 and 1.
    """
    return [
        {
            "role": "system",
            "content": "You are an AI trained to compare job descriptions with resumes. Your task is to evaluate how well a job description matches a resume and return a single numerical relevance score between 0 and 1. Provide no explanations, just the final computed score."
        },
        {
            "role": "user",
            "content": f"""
            Evaluate the given job description against the provided resume using the following criteria:

            ### 1. Role Alignment (40%)  
            - Does the resume explicitly mention job titles, responsibilities, or industries similar to the JD?  
            - Strong alignment occurs when the candidate’s past roles and responsibilities directly match the job’s key functions.  
            - Assign a score between 0 and 100%.

            ### 2. Skills Match (30%)  
            - Compare the technical and soft skills required in the JD with those mentioned in the resume.  
            - Prioritize key skills that are explicitly stated in the JD over general industry-related skills.  
            - Consider synonyms or closely related skills where applicable.  
            - Assign a score between 0 and 100%.

            ### 3. Experience Match (20%)  
            - Analyze whether the resume includes projects, achievements, or work experience relevant to the JD.  
            - Consider the depth of experience, years in relevant roles, and direct job-related accomplishments.  
            - Assign a score between 0 and 100%.

            ### 4. Education Match (5%)  
            - Check if the candidate meets the degree requirements or preferred educational background mentioned in the JD.  
            - Consider relevant certifications if explicitly listed in the JD.  
            - Assign a score between 0 and 100%.

            ### 5. Certification Match (5%)  
            - Identify whether the candidate possesses industry-recognized certifications relevant to the job (e.g., AWS, PMP, CISSP).  
            - If the JD mentions required or preferred certifications, check for their presence in the resume.  
            - Assign a score between 0 and 100%.

            **Final Score Calculation:**  
            (Role Alignment * 0.4) + (Skills Match * 0.3) + (Experience Match * 0.2) + (Education Match * 0.05) + (Certification Match * 0.05)  

            **Output Format:**  
            - Return only a single decimal number between 0 and 1, representing the weighted match score.  
            - Do not include explanations, comments, or additional text.  

            ---  

            **Job Description:**  
            {jd_text}  

            **Resume:**  
            {resume_text}  
            """
        }
    ]
