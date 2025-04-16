"""
Client for interacting with the OpenRouter API using the openai library.

Handles sending requests to OpenRouter to generate follow-up questions
based on student submissions and the configured system prompt.
Includes fallback mechanisms.
"""

import logging
from openai import OpenAI, APITimeoutError, APIConnectionError, RateLimitError, APIStatusError

from .config import get_settings

# --- Settings and Logger ---
settings = get_settings()
logger = logging.getLogger(__name__)

# --- Constants ---
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_FALLBACK_QUESTION = "Please elaborate on the main point of your submission."
DEFAULT_MODEL = "openai/gpt-3.5-turbo" # Default model if not specified elsewhere

# --- OpenAI Client Initialization ---
# The API key is read from the environment variable via settings
# DO NOT HARDCODE THE API KEY HERE
if settings.OPENROUTER_API_KEY:
    client = OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=settings.OPENROUTER_API_KEY,
    )
    logger.info("OpenAI client initialized for OpenRouter.")
else:
    client = None # Client is not initialized if key is missing
    logger.warning("OPENROUTER_API_KEY not set. OpenRouter client not initialized.")

async def generate_follow_up_question(submission_content: str, system_prompt: str) -> str:
    """
    Calls the OpenRouter API using the openai library to generate a contextual question.

    Args:
        submission_content: The text of the student's original submission.
        system_prompt: The system prompt fetched from the database.

    Returns:
        The generated question as a string, or a fallback question if the API call fails
        or the client is not initialized.
    """
    if not client:
        logger.warning("OpenRouter client not available (API key likely missing). Returning fallback question.")
        return DEFAULT_FALLBACK_QUESTION

    # Define optional headers (replace placeholders if needed)
    # You might want to make YOUR_SITE_URL and YOUR_SITE_NAME configurable via settings
    http_headers = {
        "HTTP-Referer": "https://illia-shyn.github.io/ThoughtCaptcha-frontend/", # Example placeholder
        "X-Title": "ThoughtCaptcha",              # Example placeholder
    }

    try:
        logger.debug(f"Sending request to OpenRouter model: {DEFAULT_MODEL}")
        completion = await client.chat.completions.create(
            extra_headers=http_headers,
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Student Submission:\n```\n{submission_content}\n```\nGenerate a follow-up question:"}
            ],
            max_tokens=70, # Adjusted max tokens slightly
            temperature=0.7,
            timeout=30.0 # Timeout for the request
        )

        generated_question = completion.choices[0].message.content.strip()

        if generated_question:
            logger.info(f"Successfully generated question for submission snippet: {submission_content[:50]}...")
            return generated_question
        else:
            logger.warning("OpenRouter response contained an empty message content.")
            return DEFAULT_FALLBACK_QUESTION

    except APITimeoutError:
        logger.error("OpenRouter API request timed out.")
    except APIConnectionError as e:
        logger.error(f"OpenRouter API connection error: {e}")
    except RateLimitError:
        logger.error("OpenRouter API rate limit exceeded.")
    except APIStatusError as e:
        logger.error(f"OpenRouter API status error: {e.status_code} - {e.response}")
    except Exception as e:
        logger.error(f"An unexpected error occurred calling OpenRouter: {e}", exc_info=True)

    # If any error occurred, return the fallback
    logger.warning("Returning fallback question due to API error or invalid response.")
    return DEFAULT_FALLBACK_QUESTION 