
# backend/llm_engine.py

import os
import requests


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def generate_analysis(profile, recommendations):

    if not OPENAI_API_KEY:
        return {
            "summary": "LLM disabled (no API key)",
            "risk_warning": "N/A",
            "strategy": "Rule-based only"
        }


    prompt = f"""
You are a professional crypto investment analyst.

User profile: {profile}

Portfolio:
{recommendations}

Explain:
1. Why these assets were chosen
2. Main risks
3. Market outlook
4. Strategy advice

Be concise and practical.
"""


    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }


    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a crypto analyst."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }


    res = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=30
    )


    data = res.json()

    content = data["choices"][0]["message"]["content"]

    return {
        "summary": content,
        "risk_warning": "Auto-generated",
        "strategy": "Hybrid AI"
    }
