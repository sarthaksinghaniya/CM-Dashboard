from pydantic import BaseModel, Field, field_validator
from typing import Optional

class FeedbackCreate(BaseModel):
    ticket_id: str = Field(..., description="The unique complaint ticket ID.")
    rating: int = Field(..., description="Rating score from 1 to 5.")
    remarks: Optional[str] = Field(None, description="Optional citizen remarks or notes.")

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: int) -> int:
        if v < 1 or v > 5:
            raise ValueError("Rating must be between 1 and 5.")
        return v

class FeedbackResponse(BaseModel):
    reward: float
    message: str
