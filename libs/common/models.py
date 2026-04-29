from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from libs.common.db import Base


class JobStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class JobMode(str, enum.Enum):
    transcribe_only = "transcribe_only"
    enhance_and_transcribe = "enhance_and_transcribe"


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(
            "queued", "running", "completed", "failed",
            name="job_status",
        ),
        nullable=False,
    )
    mode: Mapped[JobMode] = mapped_column(
        Enum(
            "transcribe_only", "enhance_and_transcribe",
            name="job_mode",
        ),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False, default="fake")
    preset: Mapped[str] = mapped_column(String(64), nullable=False, default="bypass")

    raw_audio_uri: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    enhanced_audio_uri: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    transcript_uri: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    transcript_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    provider_payload_uri: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
