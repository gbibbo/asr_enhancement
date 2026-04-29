"""create_jobs_table

Revision ID: 496c2c194ab1
Revises: 
Create Date: 2026-04-29 21:01:05.689120

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "496c2c194ab1"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # sa.Enum with create_type=True (default) emits CREATE TYPE before the table.
    # Explicit op.execute() CREATE TYPE calls are intentionally omitted to avoid
    # double-emission in Alembic's SQL rendering.
    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "queued", "running", "completed", "failed",
                name="job_status",
            ),
            nullable=False,
        ),
        sa.Column(
            "mode",
            sa.Enum(
                "transcribe_only", "enhance_and_transcribe",
                name="job_mode",
            ),
            nullable=False,
        ),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("preset", sa.String(64), nullable=False),
        sa.Column("raw_audio_uri", sa.String(1024), nullable=True),
        sa.Column("enhanced_audio_uri", sa.String(1024), nullable=True),
        sa.Column("transcript_uri", sa.String(1024), nullable=True),
        sa.Column("transcript_text", sa.Text(), nullable=True),
        sa.Column("provider_payload_uri", sa.String(1024), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("jobs")
    op.execute("DROP TYPE job_mode")
    op.execute("DROP TYPE job_status")
