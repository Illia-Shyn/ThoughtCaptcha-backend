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
from typing import List

from . import crud, models, schemas, openrouter_client
from .database import engine, get_db, init_db, AsyncSessionLocal
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
    # 1. Initialize database tables
    await init_db()
    logger.info("Database tables created/verified.")

    # 2. Ensure default system prompt exists (run *after* init_db)
    logger.info("Ensuring default system prompt exists...")
    async with AsyncSessionLocal() as session:
        try:
            await crud.get_system_prompt(session) # Call this to create if not exists
            await session.commit()
            logger.info("Default system prompt check complete.")
        except Exception as e:
            await session.rollback()
            logger.error(f"Error ensuring system prompt exists: {e}", exc_info=True)
            # Decide if you want the app to fail startup here or continue
            # raise e # Uncomment to make startup fail on prompt error

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

# --- Assignment Endpoints ---

@app.post("/api/assignments", response_model=schemas.AssignmentRead, status_code=status.HTTP_201_CREATED, tags=["Assignments"])
async def create_assignment(
    assignment: schemas.AssignmentCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Creates a new assignment prompt.
    Returns the created assignment record including its ID.
    """
    logger.info(f"Creating new assignment: {assignment.prompt_text[:50]}...")
    db_assignment = await crud.create_assignment(db=db, assignment=assignment)
    logger.info(f"Assignment created with ID: {db_assignment.id}")
    return db_assignment

@app.get("/api/assignments", response_model=List[schemas.AssignmentRead], tags=["Assignments"])
async def read_assignments(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve all assignment records."""
    logger.info(f"Fetching assignments with skip={skip}, limit={limit}")
    assignments = await crud.get_assignments(db, skip=skip, limit=limit)
    return assignments

@app.get("/api/assignments/current", response_model=schemas.AssignmentRead, tags=["Assignments"])
async def read_current_assignment(
    db: AsyncSession = Depends(get_db)
):
    """Retrieve the currently active assignment."""
    logger.info("Fetching current assignment")
    assignment = await crud.get_current_assignment(db)
    if not assignment:
        logger.warning("No current assignment found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No current assignment found")
    return assignment

@app.put("/api/assignments/{assignment_id}", response_model=schemas.AssignmentRead, tags=["Assignments"])
async def update_assignment(
    assignment_id: int,
    assignment_update: schemas.AssignmentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing assignment's details.
    """
    logger.info(f"Updating assignment with ID: {assignment_id}")
    db_assignment = await crud.update_assignment(db=db, assignment_id=assignment_id, assignment_update=assignment_update)
    if not db_assignment:
        logger.warning(f"Assignment ID {assignment_id} not found for update.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    return db_assignment

@app.put("/api/assignments/{assignment_id}/set-current", response_model=schemas.AssignmentRead, tags=["Assignments"])
async def set_current_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Set an assignment as the current active one and make all others not current.
    """
    logger.info(f"Setting assignment ID {assignment_id} as current")
    db_assignment = await crud.set_current_assignment(db=db, assignment_id=assignment_id)
    if not db_assignment:
        logger.warning(f"Assignment ID {assignment_id} not found when trying to set as current.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    return db_assignment

# --- Submission Endpoints ---

@app.post("/api/submit-assignment", response_model=schemas.Submission, status_code=status.HTTP_201_CREATED, tags=["Submissions"])
async def submit_assignment(
    submission: schemas.SubmissionCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Receives the initial student submission and stores it.
    Returns the created submission record including its ID.
    Can be linked to an assignment via assignment_id.
    """
    logger.info(f"Received new submission: {submission.original_content[:50]}...")
    
    # If no assignment_id is provided, try to use current assignment
    if submission.assignment_id is None:
        current_assignment = await crud.get_current_assignment(db)
        if current_assignment:
            submission.assignment_id = current_assignment.id
            logger.info(f"Using current assignment ID: {submission.assignment_id} for submission")
    
    db_submission = await crud.create_submission(db=db, submission=submission)
    logger.info(f"Submission created with ID: {db_submission.id}")
    return db_submission

@app.get("/api/submissions", response_model=List[schemas.SubmissionFullData], tags=["Submissions"])
async def read_submissions(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve all submission records (for teacher view)."""
    logger.info(f"Fetching submissions with skip={skip}, limit={limit}")
    submissions = await crud.get_all_submissions(db, skip=skip, limit=limit)
    return submissions

@app.post("/api/generate-question", response_model=schemas.QuestionGeneratedResponse, tags=["Verification"])
async def generate_question(
    request_data: schemas.QuestionGenerate,
    db: AsyncSession = Depends(get_db)
):
    """
    Generates a follow-up question for a given submission ID.
    Uses both the assignment prompt and student response for context.
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

    # Get the assignment prompt
    assignment_prompt = "No specific assignment prompt provided."
    if db_submission.assignment:
        assignment_prompt = db_submission.assignment.prompt_text
    
    # Get the student's response
    student_response = db_submission.original_content

    # Fetch the current system prompt
    system_prompt_obj = await crud.get_system_prompt(db)
    system_prompt = system_prompt_obj.prompt_text
    logger.info("Using current system prompt for question generation.")

    # Generate question using OpenRouter client, passing assignment, response and system prompt
    generated_question = await openrouter_client.generate_follow_up_question(
        assignment_prompt=assignment_prompt,
        student_response=student_response,
        system_prompt=system_prompt
    )

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

# --- Prompt Management Endpoints ---
@app.get("/api/prompt", response_model=schemas.PromptRead, tags=["Prompt Management"])
async def read_system_prompt(db: AsyncSession = Depends(get_db)):
    """Retrieve the current system prompt."""
    logger.info("Fetching current system prompt.")
    prompt = await crud.get_system_prompt(db)
    return prompt

@app.put("/api/prompt", response_model=schemas.PromptRead, tags=["Prompt Management"])
async def update_system_prompt(
    prompt_data: schemas.PromptUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update the system prompt used for generating follow-up questions."""
    logger.info(f"Updating system prompt: {prompt_data.prompt_text[:50]}...")
    updated_prompt = await crud.update_system_prompt(db=db, prompt_update=prompt_data)
    logger.info("System prompt updated successfully.")
    return updated_prompt

# Example of how to include routers from other files if the app grows:
# from .routers import items, users
# app.include_router(users.router)
# app.include_router(items.router) 