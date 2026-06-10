"""backfill missing columns for existing databases

Revision ID: 20260606_02
Revises: 20260606_01
Create Date: 2026-06-06 00:30:00
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260606_02"
down_revision: Union[str, Sequence[str], None] = "20260606_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # applications fields used by interview/status APIs
    op.execute(
        "ALTER TABLE applications ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP"
    )
    op.execute(
        "ALTER TABLE applications ADD COLUMN IF NOT EXISTS current_round_id UUID"
    )
    op.execute(
        "ALTER TABLE applications ADD COLUMN IF NOT EXISTS resume_url TEXT"
    )
    op.execute(
        "ALTER TABLE applications ADD COLUMN IF NOT EXISTS jd_url TEXT"
    )
    op.execute(
        "ALTER TABLE applications ADD COLUMN IF NOT EXISTS suitable_roles JSONB"
    )

    # Optional relation if table/column exist and constraint missing.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'applications'
                  AND column_name = 'current_round_id'
            ) AND NOT EXISTS (
                SELECT 1
                FROM information_schema.table_constraints tc
                WHERE tc.table_schema = 'public'
                  AND tc.table_name = 'applications'
                  AND tc.constraint_name = 'applications_current_round_id_fkey'
            ) THEN
                ALTER TABLE applications
                ADD CONSTRAINT applications_current_round_id_fkey
                FOREIGN KEY (current_round_id)
                REFERENCES interview_rounds(id)
                ON UPDATE RESTRICT
                ON DELETE SET NULL;
            END IF;
        END $$;
        """
    )

    # fields used by dashboard/interview-rounds APIs
    op.execute(
        "ALTER TABLE interview_rounds ADD COLUMN IF NOT EXISTS round_order INTEGER DEFAULT 1"
    )
    op.execute(
        "ALTER TABLE interview_rounds ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE"
    )

    # fields used by availability tracking API
    op.execute(
        "ALTER TABLE availability_requests ADD COLUMN IF NOT EXISTS responded_at TIMESTAMP"
    )

    # fields used by jds updates
    op.execute(
        "ALTER TABLE job_descriptions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP"
    )


def downgrade() -> None:
    # Keep downgrade safe/no-op for compatibility migration.
    pass
