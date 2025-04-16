"""
Main FastAPI Application for ThoughtCaptcha Backend.

This file defines the FastAPI app instance, includes CORS middleware,
sets up logging, defines API endpoints (routers), and potentially
includes startup/shutdown event handlers.
"""

import logging
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from . import crud, models, schemas, openrouter_client
from .database import engine, get_db, init_db
from .config import get_settings

# --- Logging Setup ---
# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Application Setup ---
settings = get_settings()

# Create FastAPI app instance
app = FastAPI(
    title="ThoughtCaptcha API",
    description="API for verifying student assignment authenticity.",
    version="0.1.0",
)

# --- CORS Middleware ---
# Set up CORS to allow requests from the frontend origin
# In production, restrict origins to your actual frontend URL
origins = [
    settings.FRONTEND_ORIGIN_URL, # From .env file
    # Add other origins if needed, e.g., localhost for development
    # "http://localhost",
    # "http://localhost:8080", # Common port for frontend dev servers
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], # Allow common methods
    allow_headers=["*"], # Allow all headers for simplicity, can be restricted
)

# --- Event Handlers (Optional) ---
@app.on_event("startup")
async def on_startup():
    """Actions to perform on application startup."""
    logger.info("Starting up ThoughtCaptcha API...")
    # Initialize database tables (consider Alembic for production)
    await init_db()
    logger.info("Database tables initialized (if they didn't exist).")
    pass # Add any other startup logic here

@app.on_event("shutdown")
async def on_shutdown():
    """Actions to perform on application shutdown."""
    logger.info("Shutting down ThoughtCaptcha API...")
    # await engine.dispose() # Clean up database engine resources
    pass

# --- API Endpoints ---

@app.get("/api/health", response_model=schemas.HealthCheckResponse, tags=["Health"])
async def health_check():
    """Simple health check endpoint."""
    return schemas.HealthCheckResponse(status="OK")

@app.post("/api/submit-assignment", response_model=schemas.Submission, status_code=status.HTTP_201_CREATED, tags=["Submissions"])
async def submit_assignment(
    submission: schemas.SubmissionCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Receives the initial student submission and stores it.
    Returns the created submission record including its ID.
    """
    logger.info(f"Received new submission: {submission.original_content[:50]}...")
    db_submission = await crud.create_submission(db=db, submission=submission)
    logger.info(f"Submission created with ID: {db_submission.id}")
    return db_submission

@app.post("/api/generate-question", response_model=schemas.QuestionGeneratedResponse, tags=["Verification"])
async def generate_question(
    request_data: schemas.QuestionGenerate,
    db: AsyncSession = Depends(get_db)
):
    """
    Generates a follow-up question for a given submission ID.
    Fetches the submission, calls OpenRouter, and stores the question.
    """
    submission_id = request_data.submission_id
    logger.info(f"Generating question for submission ID: {submission_id}")

    db_submission = await crud.get_submission(db, submission_id)
    if not db_submission:
        logger.warning(f"Submission ID {submission_id} not found for question generation.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    if db_submission.generated_question:
        logger.info(f"Question already exists for submission ID: {submission_id}. Returning existing question.")
        return schemas.QuestionGeneratedResponse(
            submission_id=submission_id,
            generated_question=db_submission.generated_question
        )

    # Generate question using OpenRouter client
    generated_question = await openrouter_client.generate_follow_up_question(db_submission.original_content)

    # Update the submission record with the generated question
    updated_submission = await crud.update_submission_question(
        db=db,
        submission_id=submission_id,
        question=generated_question
    )

    if not updated_submission:
         # This shouldn't happen if get_submission succeeded, but handle defensively
        logger.error(f"Failed to update submission {submission_id} with generated question.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save generated question")

    logger.info(f"Successfully generated and saved question for submission ID: {submission_id}")
    return schemas.QuestionGeneratedResponse(
        submission_id=submission_id,
        generated_question=generated_question
    )

@app.post("/api/verify-response", response_model=schemas.ResponseVerifiedResponse, tags=["Verification"])
async def verify_response(
    response_data: schemas.ResponseVerify,
    db: AsyncSession = Depends(get_db)
):
    """
    Receives and stores the student's response to the follow-up question.
    (Currently does not perform AI-based verification).
    """
    submission_id = response_data.submission_id
    student_response = response_data.student_response
    logger.info(f"Received response for submission ID: {submission_id}")

    # Update the submission record with the student's response
    updated_submission = await crud.update_submission_response(
        db=db,
        submission_id=submission_id,
        response=student_response
    )

    if not updated_submission:
        logger.warning(f"Submission ID {submission_id} not found when trying to store response.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    logger.info(f"Successfully stored response for submission ID: {submission_id}")
    return schemas.ResponseVerifiedResponse(submission_id=submission_id)

# Example of how to include routers from other files if the app grows:
# from .routers import items, users
# app.include_router(users.router)
# app.include_router(items.router) 