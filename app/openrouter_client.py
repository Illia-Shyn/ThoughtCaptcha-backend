"""
Client for interacting with the OpenRouter API.

Handles sending requests to OpenRouter to generate follow-up questions
based on student submissions. Includes fallback mechanisms.
"""

import httpx
import logging
from typing import Optional

from .config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
# Remember to set OPENROUTER_API_KEY in your .env file or environment variables
API_KEY = settings.OPENROUTER_API_KEY

# --- Constants ---
DEFAULT_FALLBACK_QUESTION = "Please elaborate on the main point of your submission."
DEFAULT_SYSTEM_PROMPT = ("You are an AI assistant helping to verify student understanding. "
                         "Given the student's submission text, generate one concise follow-up question "
                         "that probes their understanding or asks for clarification on a specific aspect. "
                         "The question should be answerable in 60-90 seconds.")
DEFAULT_MODEL = "openai/gpt-3.5-turbo" # A common default, adjust as needed

async def generate_follow_up_question(submission_content: str) -> str:
    """
    Calls the OpenRouter API to generate a contextual follow-up question.

    Args:
        submission_content: The text of the student's original submission.

    Returns:
        The generated question as a string, or a fallback question if the API call fails.
    """
    if not API_KEY:
        logger.warning("OPENROUTER_API_KEY is not set. Returning fallback question.")
        return DEFAULT_FALLBACK_QUESTION

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        # Optional: Add HTTP Referer or X-Title headers if recommended by OpenRouter
        # "HTTP-Referer": settings.YOUR_SITE_URL, # Replace with your actual site URL
        # "X-Title": "ThoughtCaptcha", # Replace with your app name
    }

    payload = {
        "model": DEFAULT_MODEL, # Specify the model you want to use
        "messages": [
            {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
            {"role": "user", "content": f"Student Submission:\n```\n{submission_content}\n```\nGenerate a follow-up question:"}
        ],
        "max_tokens": 50, # Limit response length
        "temperature": 0.7, # Adjust creativity vs. predictability
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client: # Increased timeout for AI generation
            response = await client.post(OPENROUTER_API_URL, headers=headers, json=payload)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

            result = response.json()
            if result.get("choices") and len(result["choices"]) > 0:
                generated_question = result["choices"][0].get("message", {}).get("content", "").strip()
                if generated_question:
                    logger.info(f"Successfully generated question for submission snippet: {submission_content[:50]}...")
                    return generated_question
                else:
                    logger.warning("OpenRouter response format unexpected or empty message content.")
            else:
                logger.warning(f"OpenRouter response did not contain expected choices: {result}")

    except httpx.RequestError as e:
        logger.error(f"HTTP Request Error calling OpenRouter: {e}")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP Status Error calling OpenRouter: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        logger.error(f"An unexpected error occurred calling OpenRouter: {e}", exc_info=True)

    # If any error occurred or the response was invalid, return the fallback
    logger.warning("Returning fallback question due to API error or invalid response.")
    return DEFAULT_FALLBACK_QUESTION 