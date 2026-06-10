"""add core hrms tables

Revision ID: 20260607_03
Revises: 20260606_02
Create Date: 2026-06-07 10:00:00
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260607_03"
down_revision: Union[str, Sequence[str], None] = "20260606_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS employees (
            id UUID PRIMARY KEY,
            employee_code VARCHAR NOT NULL UNIQUE,
            first_name VARCHAR NOT NULL,
            last_name VARCHAR NOT NULL,
            email VARCHAR NOT NULL UNIQUE,
            phone VARCHAR,
            department VARCHAR NOT NULL,
            designation VARCHAR NOT NULL,
            employment_type VARCHAR NOT NULL DEFAULT 'Full-time',
            date_of_joining DATE NOT NULL,
            manager_name VARCHAR,
            base_salary DOUBLE PRECISION NOT NULL DEFAULT 0.0,
            status VARCHAR NOT NULL DEFAULT 'Active',
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS attendance_records (
            id UUID PRIMARY KEY,
            employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE ON UPDATE RESTRICT,
            attendance_date DATE NOT NULL,
            check_in TIMESTAMP,
            check_out TIMESTAMP,
            status VARCHAR NOT NULL DEFAULT 'Present',
            work_mode VARCHAR,
            notes TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_attendance_employee_date UNIQUE (employee_id, attendance_date)
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS payroll_records (
            id UUID PRIMARY KEY,
            employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE ON UPDATE RESTRICT,
            pay_period_start DATE NOT NULL,
            pay_period_end DATE NOT NULL,
            gross_salary DOUBLE PRECISION NOT NULL DEFAULT 0.0,
            deductions DOUBLE PRECISION NOT NULL DEFAULT 0.0,
            bonuses DOUBLE PRECISION NOT NULL DEFAULT 0.0,
            net_salary DOUBLE PRECISION NOT NULL DEFAULT 0.0,
            status VARCHAR NOT NULL DEFAULT 'Pending',
            paid_on TIMESTAMP,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS performance_reviews (
            id UUID PRIMARY KEY,
            employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE ON UPDATE RESTRICT,
            review_cycle VARCHAR NOT NULL,
            reviewer_name VARCHAR NOT NULL,
            goals JSONB,
            rating DOUBLE PRECISION,
            feedback TEXT,
            strengths TEXT,
            improvements TEXT,
            review_date DATE NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS performance_reviews")
    op.execute("DROP TABLE IF EXISTS payroll_records")
    op.execute("DROP TABLE IF EXISTS attendance_records")
    op.execute("DROP TABLE IF EXISTS employees")
