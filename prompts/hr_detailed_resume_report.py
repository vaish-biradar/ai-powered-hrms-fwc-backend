def get_detailed_resume_report_prompt(jd_text: str, resume_text: str) -> list:
    """
    Generates an LLM prompt for structured, HR-friendly resume analysis against a job description.
    """
    return [
        {"role": "system", "content": "You are an AI trained to analyze resumes against job descriptions and provide a structured, HR-friendly breakdown."},
        {"role": "user", "content": f"""
            Compare the following resume against the job description (JD) and provide a **structured, concise** report.

            **Job Description (JD):**
            {jd_text}

            **Resume:**
            {resume_text}

            ---
            **Candidate Summary**
            - **Name:** [Extracted Name]
            - **Email:** [Extracted Email]
            - **Phone (if available):** [Extracted Phone]
            - **LinkedIn (if available):** [Extracted LinkedIn]
            - **Current Job Title:** [Extracted Title]  
            - **Experience:** [X years or Fresher]

            ---
            **Education & Certifications**
            - **Degree:** [Most Relevant Degree]  
            - **Certifications:** [Relevant Certifications]  
            - **Alignment with JD:** [High/Moderate/Low]

            ---
            **Skill Matching**
            | Skill  | JD | Resume | Match |
            |--------|----|--------|-------|
            | Skill1 | ✅  | ✅      | ✔     |
            | Skill2 | ✅  | ❌      | ❌    |
            | Skill3 | ✅  | ✅      | ✔     |
            | Extra  | -   | ✅      | ⭐     |

            ---
            **Work Experience**
            - **Relevant Job:** [Job Title] at [Company]  
            - **Industry Exp.:** [X years]  
            - **Alignment:** [High/Moderate/Low]  
            - **Relevance Score:** [1-10]  

            ---
            **Gaps & Areas for Improvement**
            - **Missing Skills:** [List missing skills]  
            - **Experience Gaps:** [Mention missing relevant roles/tools]  

            Ensure the response is **structured, concise, and easy for HRs to evaluate** with **clear bullet points and tables** in markdown format.
        """}
    ]




def get_detailed_resume_pdfreport_prompt(jd_text: str, resume_text: str) -> list:
    """
    Generates the LLM prompt for analyzing a resume against a job description.
    """
    return [
        {"role": "system", "content": "You are an AI trained to analyze resumes against job descriptions and provide a structured breakdown."},
        {"role": "user", "content": f"""
            Analyze the following resume against the given job description (JD) and provide a structured and detailed analysis:

            **Job Description (JD):**
            {jd_text}

            **Resume:**
            {resume_text}

            ### Provide a comprehensive analysis including:

            1. **Candidate Information**:
               - Extract the candidate's full name and email.
               - Identify their current job title (if available).
               - Total Year of Experience (if available) otherwise Fresher

            2. **Education & Certifications**:
               - Summarize degrees, certifications, and other academic credentials.
               - Highlight relevant qualifications required for the role.

            3. **Skill Matches (Table Format)**:
               - Compare required skills from the JD with the candidate's skills from the resume.
               - Present findings in a structured table format.

            **Skill Matches Table:**
            | Skill | Required in JD | Mentioned in Resume | Match (✔/❌) |
            |-------|---------------|---------------------|--------------|
            | [Skill 1] | ✅ | ✅ | ✔ |
            | [Skill 2] | ✅ | ❌ | ❌ |
            | [Skill 3] | ✅ | ✅ | ✔ |
            | [Skill 4] | ✅ | ❌ | ❌ |
            | Additional Skills | - | ✅ | Extra |

            4. **Work Experience & Role Alignment**:
               - Summarize the candidates work history, focusing on relevant job titles and responsibilities.
               - Assess how well past roles align with the JD in terms of industry, responsibilities, and seniority level.

            5. **Identified Gaps & Areas for Improvement**:
               - Highlight missing skills, experiences, or qualifications.
               - Mention areas where the candidate lacks required certifications, tools, or industry exposure.

            Ensure the response is **structured, easy to read, and HR-friendly** with clear bullet points and tables.
        """}
    ]
