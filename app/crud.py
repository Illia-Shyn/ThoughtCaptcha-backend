"""
CRUD (Create, Read, Update, Delete) Operations for Submissions.

This module provides functions to interact with the Submission model
in the database, encapsulating the database logic.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload # If needed for relationships later
from sqlalchemy import desc # For ordering submissions

from . import models, schemas

async def create_submission(db: AsyncSession, submission: schemas.SubmissionCreate) -> models.Submission:
    """
    Creates a new submission record in the database.
    """
    db_submission = models.Submission(
        original_content=submission.original_content
    )
    db.add(db_submission)
    await db.flush() # Flush to get the ID before returning
    await db.refresh(db_submission)
    return db_submission

async def get_submission(db: AsyncSession, submission_id: int) -> models.Submission | None:
    """
    Retrieves a specific submission by its ID.
    """
    result = await db.execute(select(models.Submission).filter(models.Submission.id == submission_id))
    return result.scalars().first()

async def get_all_submissions(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[models.Submission]:
    """Retrieves a list of all submissions, newest first."""
    result = await db.execute(
        select(models.Submission)
        .order_by(desc(models.Submission.created_at))
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def update_submission_question(db: AsyncSession, submission_id: int, question: str) -> models.Submission | None:
    """
    Updates the generated_question field for a specific submission.
    Returns the updated submission object or None if not found.
    """
    db_submission = await get_submission(db, submission_id)
    if db_submission:
        db_submission.generated_question = question
        db.add(db_submission)
        await db.flush()
        await db.refresh(db_submission)
    return db_submission

async def update_submission_response(db: AsyncSession, submission_id: int, response: str) -> models.Submission | None:
    """
    Updates the student_response field for a specific submission.
    Returns the updated submission object or None if not found.
    """
    db_submission = await get_submission(db, submission_id)
    if db_submission:
        db_submission.student_response = response
        db.add(db_submission)
        await db.flush()
        await db.refresh(db_submission)
    return db_submission

# Potential future CRUD functions:
# async def get_submissions(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[models.Submission]:
#     """Retrieves a list of submissions."""
#     result = await db.execute(select(models.Submission).offset(skip).limit(limit))
#     return result.scalars().all()
#
# async def delete_submission(db: AsyncSession, submission_id: int) -> bool:
#     """Deletes a submission by ID. Returns True if deleted, False otherwise."""
#     db_submission = await get_submission(db, submission_id)
#     if db_submission:
#         await db.delete(db_submission)
#         await db.flush()
#         return True
#     return False

# --- System Prompt CRUD ---

async def get_system_prompt(db: AsyncSession) -> models.SystemPrompt:
    """
    Retrieves the system prompt. If it doesn't exist, creates it with the default.
    Ensures only one prompt exists with ID=1.
    """
    # Try to get the prompt with ID 1
    result = await db.execute(select(models.SystemPrompt).filter(models.SystemPrompt.id == 1))
    db_prompt = result.scalars().first()

    if not db_prompt:
        # If not found, create it with the default value from the model
        db_prompt = models.SystemPrompt(id=1)
        db.add(db_prompt)
        await db.flush() # Use flush + refresh to get the object back with defaults applied
        await db.refresh(db_prompt)
    return db_prompt

async def update_system_prompt(db: AsyncSession, prompt_update: schemas.PromptUpdate) -> models.SystemPrompt:
    """
    Updates the system prompt (identified by fixed ID=1).
    """
    db_prompt = await get_system_prompt(db) # Use get_system_prompt to ensure it exists
    db_prompt.prompt_text = prompt_update.prompt_text
    db.add(db_prompt)
    await db.flush()
    await db.refresh(db_prompt)
    return db_prompt 