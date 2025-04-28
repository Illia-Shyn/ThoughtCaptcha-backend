"""
Pydantic Schemas for ThoughtCaptcha API.

These schemas define the structure and validation rules for data
transferred through the API (request bodies, response models).
"""

import datetime
from pydantic import BaseModel, Field
from typing import Optional

# --- Assignment Schemas ---
class AssignmentBase(BaseModel):
    """Base schema for assignment data."""
    prompt_text: str = Field(..., description="The text of the assignment question/prompt.")
    is_current: Optional[bool] = False

class AssignmentCreate(AssignmentBase):
    """Schema for creating a new assignment record."""
    pass

class AssignmentUpdate(BaseModel):
    """Schema for updating an assignment record (allows partial updates)."""
    prompt_text: Optional[str] = None
    is_current: Optional[bool] = None

class AssignmentRead(AssignmentBase):
    """Schema for representing an Assignment record in API responses."""
    id: int
    created_at: datetime.datetime
    updated_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True

# --- Base Schemas ---
class SubmissionBase(BaseModel):
    """Base schema for submission data, used for creation."""
    original_content: str = Field(..., description="The initial content submitted by the student.")

class SubmissionCreate(SubmissionBase):
    """Schema for creating a new submission record."""
    assignment_id: Optional[int] = None

class QuestionGenerate(BaseModel):
    """Schema for the request to generate a follow-up question."""
    submission_id: int = Field(..., description="The ID of the submission to generate a question for.")

class ResponseVerify(BaseModel):
    """Schema for submitting the student's response to the follow-up question."""
    submission_id: int = Field(..., description="The ID of the submission this response belongs to.")
    student_response: str = Field(..., description="The student's answer to the follow-up question.")

# --- Prompt Schemas ---
class PromptBase(BaseModel):
    prompt_text: str

class PromptUpdate(PromptBase):
    pass

class PromptRead(PromptBase):
    id: int = 1 # Usually fixed at 1
    # updated_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True

# --- Response Schemas ---
class Submission(SubmissionBase):
    """Schema for representing a Submission record in API responses."""
    id: int
    generated_question: Optional[str] = None
    student_response: Optional[str] = None
    assignment_id: Optional[int] = None
    created_at: datetime.datetime
    updated_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True # Renamed from orm_mode in Pydantic v2

class SubmissionFullData(Submission):
    """Schema for retrieving full submission data for teacher view."""
    assignment: Optional[AssignmentRead] = None
    
    class Config:
        from_attributes = True

class QuestionGeneratedResponse(BaseModel):
    """Response schema after successfully generating a question."""
    submission_id: int
    generated_question: str

class ResponseVerifiedResponse(BaseModel):
    """Response schema after successfully verifying (storing) a response."""
    submission_id: int
    message: str = "Response recorded successfully."

# --- Health Check Schema ---
class HealthCheckResponse(BaseModel):
    """Schema for the health check endpoint response."""
    status: str = "OK" 