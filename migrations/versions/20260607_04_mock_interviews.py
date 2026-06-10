"""add mock interviews table

Revision ID: 20260607_04
Revises: 20260607_03
Create Date: 2026-06-07 16:30:00
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260607_04"
down_revision: Union[str, Sequence[str], None] = "20260607_03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS mock_interviews (
            id UUID PRIMARY KEY,
            resume_id UUID REFERENCES resumes(id) ON DELETE SET NULL ON UPDATE RESTRICT,
            job_description_id UUID NOT NULL REFERENCES job_descriptions(id) ON DELETE CASCADE ON UPDATE RESTRICT,
            candidate_name VARCHAR,
            candidate_email VARCHAR,
            transcript_text TEXT NOT NULL,
            conversation JSONB NOT NULL,
            status VARCHAR NOT NULL DEFAULT 'completed',
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS mock_interviews")
