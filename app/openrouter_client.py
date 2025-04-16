"""
Client for interacting with the OpenRouter API using direct HTTP requests.

Handles sending requests to OpenRouter to generate follow-up questions
based on student submissions and the configured system prompt.
Includes fallback mechanisms.
"""

import logging
import json
import requests
import asyncio
from typing import Dict, List, Any

from .config import get_settings

# --- Settings and Logger ---
settings = get_settings()
logger = logging.getLogger(__name__)

# --- Constants ---
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_FALLBACK_QUESTION = "Please elaborate on the main point of your submission."
FREE_MODEL = "deepseek/deepseek-chat-v3-0324:free"  # Using explicitly free model

async def generate_follow_up_question(submission_content: str, system_prompt: str) -> str:
    """
    Calls the OpenRouter API using direct HTTP requests to generate a contextual question.

    Args:
        submission_content: The text of the student's original submission.
        system_prompt: The system prompt fetched from the database.

    Returns:
        The generated question as a string, or a fallback question if the API call fails.
    """
    if not settings.OPENROUTER_API_KEY:
        logger.warning("OPENROUTER_API_KEY not set. Returning fallback question.")
        return DEFAULT_FALLBACK_QUESTION

    # Define headers
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://illia-shyn.github.io/ThoughtCaptcha-frontend/",
        "X-Title": "ThoughtCaptcha",
    }

    # Create request payload
    payload = {
        "model": FREE_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Student Submission:\n```\n{submission_content}\n```\nGenerate a follow-up question:"}
        ],
        "max_tokens": 70,
        "temperature": 0.7
    }

    # Using asyncio.to_thread to run the requests call asynchronously
    try:
        # Run the HTTP request in a thread to not block the event loop
        response = await asyncio.to_thread(
            requests.post,
            url=OPENROUTER_API_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=30.0
        )

        # Process the response
        if response.status_code == 200:
            response_data = response.json()
            if response_data and "choices" in response_data and len(response_data["choices"]) > 0:
                generated_question = response_data["choices"][0]["message"]["content"].strip()
                if generated_question:
                    logger.info(f"Successfully generated question for submission snippet: {submission_content[:50]}...")
                    return generated_question

            logger.warning("OpenRouter response did not contain the expected data structure.")
            return DEFAULT_FALLBACK_QUESTION
        else:
            logger.error(f"OpenRouter API status error: {response.status_code} - {response}")
            return DEFAULT_FALLBACK_QUESTION

    except requests.exceptions.Timeout:
        logger.error("OpenRouter API request timed out.")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"OpenRouter API connection error: {e}")
    except json.JSONDecodeError:
        logger.error("Failed to parse OpenRouter API response as JSON.")
    except Exception as e:
        logger.error(f"An unexpected error occurred calling OpenRouter: {e}", exc_info=True)

    # If any error occurred, return the fallback
    logger.warning("Returning fallback question due to API error or invalid response.")
    return DEFAULT_FALLBACK_QUESTION 