"""
Pydantic Schemas for ThoughtCaptcha API.

These schemas define the structure and validation rules for data
transferred through the API (request bodies, response models).
"""

import datetime
from pydantic import BaseModel, Field
from typing import Optional

# --- Base Schemas ---
class SubmissionBase(BaseModel):
    """Base schema for submission data, used for creation."""
    original_content: str = Field(..., description="The initial content submitted by the student.")

class SubmissionCreate(SubmissionBase):
    """Schema for creating a new submission record."""
    pass # Inherits original_content

class QuestionGenerate(BaseModel):
    """Schema for the request to generate a follow-up question."""
    submission_id: int = Field(..., description="The ID of the submission to generate a question for.")

class ResponseVerify(BaseModel):
    """Schema for submitting the student's response to the follow-up question."""
    submission_id: int = Field(..., description="The ID of the submission this response belongs to.")
    student_response: str = Field(..., description="The student's answer to the follow-up question.")

# --- Response Schemas ---
class Submission(SubmissionBase):
    """Schema for representing a Submission record in API responses."""
    id: int
    generated_question: Optional[str] = None
    student_response: Optional[str] = None
    created_at: datetime.datetime
    updated_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True # Renamed from orm_mode in Pydantic v2

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