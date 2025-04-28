"""
SQLAlchemy Database Models for ThoughtCaptcha.

Defines the structure of the database tables used to store
assignment submissions, generated questions, and student responses.
"""

import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func, Boolean
from sqlalchemy.orm import relationship

from .database import Base

# --- Constants for default prompt ---
DEFAULT_SYSTEM_PROMPT = ("You are an AI assistant helping to verify student understanding. "
                         "You will receive the original assignment question and the student's response to it. "
                         "Based on BOTH the question and the response, generate ONE concise follow-up question "
                         "that probes the student's understanding of their response *in relation to the assignment*, or asks for clarification on a specific aspect connecting the two. "
                         "The follow-up question should be answerable in 60-90 seconds.")

class Assignment(Base):
    """
    Represents an assignment prompt set by the teacher.
    Only one assignment can be marked as current.
    """
    __tablename__ = "assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    prompt_text = Column(Text, nullable=False)
    is_current = Column(Boolean, default=False, index=True) # Flag for the currently active assignment
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    # Relationship to submissions
    submissions = relationship("Submission", back_populates="assignment")

class Submission(Base):
    """
    Represents an individual submission cycle, linking the original
    submission, the generated question, and the final response.
    """
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    # For simplicity, storing the original submission directly.
    # In a real app, this might be a file path or reference.
    original_content = Column(Text, nullable=False)
    generated_question = Column(Text, nullable=True) # Nullable until generated
    student_response = Column(Text, nullable=True) # Nullable until provided
    # Consider adding an authenticity score later if needed
    # authenticity_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Link to the assignment
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=True)
    assignment = relationship("Assignment", back_populates="submissions")

    # We could add relationships to User or Assignment models later if needed
    # user_id = Column(Integer, ForeignKey("users.id"))
    # user = relationship("User")

class SystemPrompt(Base):
    """
    Stores the system prompt used for generating follow-up questions.
    Uses a fixed ID (1) to ensure only one row exists.
    """
    __tablename__ = "system_prompts"

    id = Column(Integer, primary_key=True, default=1)
    prompt_text = Column(Text, nullable=False, default=DEFAULT_SYSTEM_PROMPT)
    # updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

# Example of how other models could be added:
# class User(Base):
#     __tablename__ = "users"
#     id = Column(Integer, primary_key=True, index=True)
#     username = Column(String, unique=True, index=True)
#     # ... other user fields 