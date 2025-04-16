"""
SQLAlchemy Database Models for ThoughtCaptcha.

Defines the structure of the database tables used to store
assignment submissions, generated questions, and student responses.
"""

import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from .database import Base

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

    # We could add relationships to User or Assignment models later if needed
    # user_id = Column(Integer, ForeignKey("users.id"))
    # user = relationship("User")

# Example of how other models could be added:
# class User(Base):
#     __tablename__ = "users"
#     id = Column(Integer, primary_key=True, index=True)
#     username = Column(String, unique=True, index=True)
#     # ... other user fields 