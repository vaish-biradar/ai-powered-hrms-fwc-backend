def get_job_details_prompt(jd_text: str) -> list:
    """
    Generates an LLM prompt to extract structured job details such as title, department, employment type, location, experience level, 
    a concise one-sentence summary, and the most important required skills (top 3-4 only).
    Department must be categorized as Technology for Oracle EPM, OneStream, and general IT/technology roles.
    Location should be explicitly mentioned or noted as 'Not mentioned'.
    """
    return [
        {
            "role": "system",
            "content": "You are an AI specialized in analyzing job descriptions. Your task is to extract structured job details including job title, department (must be: Technology for Oracle EPM, OneStream, and general technology or IT services), employment type, location (if mentioned, provide it; otherwise, say 'Not mentioned'), experience level, a one-sentence summary, and the topmost required skills (only the most important 3-4 skills)."
        },
        {
            "role": "user",
            "content": f"""
                Analyze the following job description and extract the details in the given format:  
                
                **Title:** <Extracted Job Title>  
                **Department:** <Technology or Not mentioned>  
                **Employment Type:** <Full-time/Part-time/Contract>  
                **Location:** <Job Location or 'Not mentioned'>  
                **Experience Level:** <Years of Experience Required>  
                **Summary:** <One-sentence concise job description>  
                **Required Skills:** <Top 3-4 most important skills only, comma-separated>  

                **Job Description:**  
                {jd_text}
            """
        }
    ]
