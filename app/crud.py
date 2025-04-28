"""
CRUD (Create, Read, Update, Delete) Operations for Submissions and Assignments.

This module provides functions to interact with the database models,
encapsulating the database logic.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload 
from sqlalchemy import desc, update

from . import models, schemas

# --- Assignment CRUD Operations ---

async def create_assignment(db: AsyncSession, assignment: schemas.AssignmentCreate) -> models.Assignment:
    """
    Creates a new assignment record in the database.
    """
    db_assignment = models.Assignment(
        prompt_text=assignment.prompt_text,
        is_current=assignment.is_current
    )
    db.add(db_assignment)
    await db.flush()
    await db.refresh(db_assignment)
    
    # If this assignment is set as current, ensure all others are not current
    if db_assignment.is_current:
        await set_current_assignment(db, db_assignment.id)
    
    return db_assignment

async def get_assignment(db: AsyncSession, assignment_id: int) -> models.Assignment | None:
    """
    Retrieves a specific assignment by its ID.
    """
    result = await db.execute(select(models.Assignment).filter(models.Assignment.id == assignment_id))
    return result.scalars().first()

async def get_assignments(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[models.Assignment]:
    """
    Retrieves a list of all assignments, ordered by creation date (newest first).
    """
    result = await db.execute(
        select(models.Assignment)
        .order_by(desc(models.Assignment.created_at))
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def get_current_assignment(db: AsyncSession) -> models.Assignment | None:
    """
    Finds the assignment where is_current is True.
    """
    result = await db.execute(select(models.Assignment).filter(models.Assignment.is_current == True))
    return result.scalars().first()

async def update_assignment(db: AsyncSession, assignment_id: int, assignment_update: schemas.AssignmentUpdate) -> models.Assignment | None:
    """
    Updates an assignment record.
    Returns the updated assignment object or None if not found.
    """
    db_assignment = await get_assignment(db, assignment_id)
    if not db_assignment:
        return None
    
    # Update fields if provided
    if assignment_update.prompt_text is not None:
        db_assignment.prompt_text = assignment_update.prompt_text
    
    if assignment_update.is_current is not None:
        db_assignment.is_current = assignment_update.is_current
        # If setting this as current, ensure others are not current
        if assignment_update.is_current:
            await set_current_assignment(db, assignment_id)
    
    db.add(db_assignment)
    await db.flush()
    await db.refresh(db_assignment)
    return db_assignment

async def set_current_assignment(db: AsyncSession, assignment_id: int) -> models.Assignment | None:
    """
    Sets the specified assignment's is_current to True and all others to False.
    Returns the current assignment or None if not found.
    """
    # First, set all assignments to not current
    await db.execute(
        update(models.Assignment)
        .where(models.Assignment.id != assignment_id)
        .values(is_current=False)
    )
    
    # Then set the specified one to current
    db_assignment = await get_assignment(db, assignment_id)
    if db_assignment:
        db_assignment.is_current = True
        db.add(db_assignment)
        await db.flush()
        await db.refresh(db_assignment)
    
    return db_assignment

# --- Submission CRUD Operations ---

async def create_submission(db: AsyncSession, submission: schemas.SubmissionCreate) -> models.Submission:
    """
    Creates a new submission record in the database.
    """
    db_submission = models.Submission(
        original_content=submission.original_content,
        assignment_id=submission.assignment_id
    )
    db.add(db_submission)
    await db.flush() # Flush to get the ID before returning
    await db.refresh(db_submission)
    return db_submission

async def get_submission(db: AsyncSession, submission_id: int) -> models.Submission | None:
    """
    Retrieves a specific submission by its ID, including its assignment.
    """
    result = await db.execute(
        select(models.Submission)
        .options(selectinload(models.Submission.assignment))
        .filter(models.Submission.id == submission_id)
    )
    return result.scalars().first()

async def get_all_submissions(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[models.Submission]:
    """
    Retrieves a list of all submissions, newest first, including their assignments.
    """
    result = await db.execute(
        select(models.Submission)
        .options(selectinload(models.Submission.assignment))
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