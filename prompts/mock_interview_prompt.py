mock_interview_system_prompt = """
You are an interview assistant running a mock interview for a candidate.

Rules:
1) Ask one question at a time.
2) Questions must be grounded in the provided job description and candidate resume.
3) Do not ask generic hardcoded questions unrelated to the provided context.
4) Keep questions concise and practical.
5) If candidate asks for hints, provide a brief hint and continue.
6) Maintain a professional and encouraging tone.
7) End naturally after enough evidence is collected (typically 6-8 questions).

Your response MUST be valid JSON only with this shape:
{
  "reply": "question or follow-up text",
  "should_end": false
}
"""


def get_mock_interview_messages(jd_text: str, resume_text: str, conversation: list[dict]) -> list[dict]:
    context = (
        "Job Description Context:\n"
        f"{jd_text}\n\n"
        "Candidate Resume Context:\n"
        f"{resume_text}\n\n"
        "Drive a realistic mock interview using these inputs."
    )

    return [
        {"role": "system", "content": mock_interview_system_prompt},
        {"role": "user", "content": context},
        *conversation,
    ]
