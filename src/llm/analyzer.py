from litellm import completion
from typing import List, Dict
import os

def format_experience_for_llm(experience_entries: List[Dict]) -> str:
    """Format experience data for LLM analysis"""
    if not experience_entries:
        return "No professional experience information found."

    formatted_text = "PROFESSIONAL EXPERIENCE:\n\n"

    for i, job in enumerate(experience_entries, 1):
        formatted_text += f"--- Position {i} ---\n"
        formatted_text += f"Job Title: {job.get('title', 'Not specified')}\n"
        formatted_text += f"Company: {job.get('company', 'Not specified')}\n"
        if job.get("employment_type"):
            formatted_text += f"Employment Type: {job.get('employment_type')}\n"
        formatted_text += f"Duration: {job.get('duration', 'Not specified')}\n"
        if job.get("location"):
            formatted_text += f"Location: {job.get('location')}\n"
        formatted_text += f"Description & Responsibilities:\n{job.get('description', 'No description available')}\n\n"

    return formatted_text

def analyze_candidate_experience(experience_text: str, search_query: str) -> str:
    """Analyze candidate experience using LLM"""
    model = os.getenv("LLM_MODEL_NAME")
    if not model:
        raise ValueError("❌ LLM_MODEL_NAME not set. Set the environment variable or pass explicitly.")

    prompt = f"""
You're an expert tech recruiter reviewing a candidate's professional experience for {search_query}.

Analyze the work experience carefully, considering:
- Actual job titles and progression
- Company types and reputation
- Duration of employment (longer tenure indicates stability)
- Specific technologies, frameworks, and tools mentioned
- Hands-on development responsibilities vs. academic/theoretical knowledge
- Career progression and growth

Based on the professional experience below, provide a concise assessment of whether this candidate should be shortlisted for {search_query}. Focus on REAL professional experience, not education or training.

Professional Experience:
\"\"\"
{experience_text}
\"\"\"

Provide your recommendation in this format:
RECOMMENDATION: [SHORTLIST/REJECT]
REASON: [Brief justification focusing on relevant experience and professional background]
"""

    response = completion(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that evaluates developer resumes.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=300,
    )
    return response.choices[0].message.content 