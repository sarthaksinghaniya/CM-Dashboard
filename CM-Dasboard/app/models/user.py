import enum
from typing import List, Optional
from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel

class RoleEnum(str, enum.Enum):
    CITIZEN = "CITIZEN"
    OFFICER = "OFFICER"
    HEAD = "HEAD"
    ADMIN = "ADMIN"

class User(BaseModel):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    password: Mapped[Optional[str]] = mapped_column(String, nullable=True) # password-less OTP is primary, but password field allowed for fallback
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), default=RoleEnum.CITIZEN, nullable=False)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    district: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    comments: Mapped[List["Comment"]] = relationship(
        "Comment",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    updates: Mapped[List["ComplaintUpdate"]] = relationship(
        "ComplaintUpdate",
        back_populates="updater",
        cascade="all, delete-orphan"
    )
    feedbacks: Mapped[List["Feedback"]] = relationship(
        "Feedback",
        back_populates="citizen",
        cascade="all, delete-orphan"
    )
    assigned_complaints: Mapped[List["Complaint"]] = relationship(
        "Complaint",
        back_populates="assigned_officer",
        foreign_keys="[Complaint.assigned_to]"
    )
