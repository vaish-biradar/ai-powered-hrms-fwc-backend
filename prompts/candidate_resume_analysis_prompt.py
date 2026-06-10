def get_resume_analysis_prompt(jd_text: str, resume_text: str, similarity: float, jd_title: str) -> list:
    """
    Generates a structured LLM prompt for resume analysis against job descriptions,
    providing candidates with clear, actionable feedback on their resume's alignment with the job.
    
    Parameters:
    - jd_text (str): The full job description text
    - resume_text (str): The candidate's resume text
    - similarity (float): The calculated similarity/match score (0-100)
    - jd_title (str): The title of the job position
    
    Returns:
    - list: A list of dictionaries containing the prompt structure for the LLM
    """
    return [
        {"role": "system", "content": """You are a Technical Hiring Assistant AI that evaluates resumes against job descriptions. 
         Your goal is to provide structured, actionable feedback that helps candidates understand exactly where their resume matches and where it falls short. 
         Focus on being specific and concrete rather than general. Format your response in clean Markdown and keep it concise yet comprehensive. it must be easy to read for the candidate"""},

        {"role": "user", "content": f"""
            Compare the following resume against the job description (JD) and provide a **structured, concise** report.

            **Resume:**
            {resume_text}
            
            **Job Description (JD):**
            {jd_text}


        ---

        ### 🔍 **Key Skills Assessment**  
        | Skill  | JD | Resume | Match |
        |--------|------|-----------|-------|
        | Skill1 | ✅   | ✅        | ✔     |
        | Skill2 | ✅   | ❌        | ❌    |
        | Skill3 | ✅   | ✅        | ✔     |
        | Extra  | -    | ✅        | ⭐     |

        ---

        ### 📈 **Experience Level Match**  
        - **Required Experience:** _(Extracted from JD)_  
        - **Your Profile:** _(Assessment based on resume)_  
        - **Gap Analysis:** _(Specific notes on alignment and discrepancies)_  

        ---

        ### 📂 **Project Relevance**  
        - 🟢 How your projects align with the JD responsibilities  
        - 🔵 Areas where alignment can be improved  
        - 🟠 Concrete suggestions for emphasizing relevant project experience  

        ---

        ### ⚠️ **Areas for Improvement**  
        - **❌ Missing Keywords:** _(Specific terms from JD missing in your resume)_  
        - **⚡ Experience Gaps:** _(Key experience areas that need enhancement)_  
        - **🎨 Presentation Issues:** _(How to better structure and showcase your skills)_  

        ---

        ### 🚀 **Action Plan to Improve Your Score**  
        #### 📚 Skill Development  
        1. 🎓 Relevant **certifications or courses** to bridge gaps  
        2. 💡 Project ideas to build the missing skills  

        ---

                    """} 
    ]