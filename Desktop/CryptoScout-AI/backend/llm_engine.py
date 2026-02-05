
# backend/llm_engine.py

import os
import json
import time
import logging
import re

from openai import OpenAI


# --------------------------------------------------
# CONFIG
# --------------------------------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

logger = logging.getLogger("LLM_ENGINE")


MAX_RETRIES = 2


# --------------------------------------------------
# UTILS
# --------------------------------------------------

def _extract_json(text: str):

    if not text:
        raise ValueError("Empty response")

    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        raise ValueError("No JSON found")

    return json.loads(match.group())


# --------------------------------------------------
# MAIN LLM INTERFACE
# --------------------------------------------------

def generate_analysis(profile: str, recommendations: list) -> dict:

    if not OPENAI_API_KEY:
        return {
            "summary": "AI disabled",
            "risk_warning": "No API key",
            "strategy": "Rule-based only"
        }


    prompt = f"""
You are a professional crypto investment analyst.

Return ONLY valid JSON.

Format:

{{
  "summary": string,
  "risk_warning": string,
  "strategy": string
}}

User profile: {profile}

Portfolio:
{json.dumps(recommendations, indent=2)}
"""


    for attempt in range(1, MAX_RETRIES + 1):

        try:

            response = client.chat.completions.create(

                model="gpt-4o-mini",

                messages=[
                    {
                        "role": "system",
                        "content": "You are a senior crypto analyst. Return ONLY JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

                temperature=0.2,
                max_tokens=400,
                timeout=30
            )


            raw = response.choices[0].message.content.strip()

            result = _extract_json(raw)

            return result


        except Exception as e:

            logger.warning(
                "LLM attempt %s failed: %s",
                attempt,
                str(e)
            )

            time.sleep(1)


    # Final fallback
    return {
        "summary": "AI temporarily unavailable",
        "risk_warning": "Use caution",
        "strategy": "Hold"
    }
