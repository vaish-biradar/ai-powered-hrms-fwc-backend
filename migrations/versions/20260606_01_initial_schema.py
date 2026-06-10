"""initial schema

Revision ID: 20260606_01
Revises:
Create Date: 2026-06-06 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260606_01"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "resumes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("summary", sa.String(), nullable=True),
        sa.Column("experience_status", sa.String(), nullable=True),
        sa.Column("years_of_experience", sa.String(), nullable=True),
        sa.Column("suitable_roles", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("path", sa.String(), nullable=True),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "job_descriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("text", sa.String(), nullable=True),
        sa.Column("department", sa.String(), nullable=True),
        sa.Column("employment_type", sa.String(), nullable=True),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("experience_level", sa.String(), nullable=True),
        sa.Column("summary", sa.String(), nullable=True),
        sa.Column("skills", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("path", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("total_openings", sa.Integer(), nullable=True),
        sa.Column("occupied_openings", sa.Integer(), nullable=True),
        sa.Column("submitted_by", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "interview_rounds",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("round_name", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("round_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "members",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("department", sa.String(), nullable=True),
        sa.Column("role", sa.String(), nullable=True),
        sa.Column("expertise", sa.String(), nullable=True),
        sa.Column("invitation_token", sa.String(), nullable=True),
        sa.Column("invitation_status", sa.String(), nullable=True),
        sa.Column("invitation_expiry", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "panels",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("panel_name", sa.String(), nullable=True),
        sa.Column("department", sa.String(), nullable=True),
        sa.Column("positions", sa.String(), nullable=True),
        sa.Column("interviews_completed", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "dashboard_stats",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("month_year", sa.String(), nullable=True),
        sa.Column("resumes", sa.Integer(), nullable=True),
        sa.Column("job_descriptions", sa.Integer(), nullable=True),
        sa.Column("applications", sa.Integer(), nullable=True),
        sa.Column("hired", sa.Integer(), nullable=True),
        sa.Column("applied_date", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("job_description_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_name", sa.String(), nullable=True),
        sa.Column("candidate_email", sa.String(), nullable=True),
        sa.Column("candidate_phone", sa.String(), nullable=True),
        sa.Column("total_experience", sa.String(), nullable=True),
        sa.Column("current_ctc", sa.String(), nullable=True),
        sa.Column("expected_ctc", sa.String(), nullable=True),
        sa.Column("current_company", sa.String(), nullable=True),
        sa.Column("current_location", sa.String(), nullable=True),
        sa.Column("current_job_title", sa.String(), nullable=True),
        sa.Column("notice_period", sa.String(), nullable=True),
        sa.Column("resume_url", sa.String(), nullable=True),
        sa.Column("job_title", sa.String(), nullable=True),
        sa.Column("jd_url", sa.String(), nullable=True),
        sa.Column("report_url", sa.String(), nullable=True),
        sa.Column("suitable_roles", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("similarity", sa.Float(), nullable=True),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("current_round_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("applied_date", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["current_round_id"], ["interview_rounds.id"], ondelete="SET NULL", onupdate="RESTRICT"),
        sa.ForeignKeyConstraint(["job_description_id"], ["job_descriptions.id"], ondelete="RESTRICT", onupdate="RESTRICT"),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="RESTRICT", onupdate="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_description_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["job_description_id"], ["job_descriptions.id"], ondelete="RESTRICT", onupdate="RESTRICT"),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="RESTRICT", onupdate="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "member_panels",
        sa.Column("member_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("panel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["member_id"], ["members.id"], ondelete="CASCADE", onupdate="RESTRICT"),
        sa.ForeignKeyConstraint(["panel_id"], ["panels.id"], ondelete="CASCADE", onupdate="RESTRICT"),
        sa.PrimaryKeyConstraint("member_id", "panel_id"),
    )

    op.create_table(
        "availability_requests",
        sa.Column("token", sa.String(), nullable=False),
        sa.Column("member_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("round_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_date", sa.DateTime(), nullable=True),
        sa.Column("requested_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("response", sa.String(), nullable=True),
        sa.Column("responded_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE", onupdate="RESTRICT"),
        sa.ForeignKeyConstraint(["member_id"], ["members.id"], ondelete="CASCADE", onupdate="RESTRICT"),
        sa.ForeignKeyConstraint(["requested_by_id"], ["members.id"], ondelete="SET NULL", onupdate="RESTRICT"),
        sa.ForeignKeyConstraint(["round_id"], ["interview_rounds.id"], ondelete="CASCADE", onupdate="RESTRICT"),
        sa.PrimaryKeyConstraint("token"),
    )

    op.create_table(
        "interviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("round_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("panel_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("scheduled_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("scheduled_date", sa.DateTime(), nullable=True),
        sa.Column("meeting_link", sa.String(), nullable=True),
        sa.Column("meeting_location", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE", onupdate="RESTRICT"),
        sa.ForeignKeyConstraint(["panel_id"], ["panels.id"], ondelete="SET NULL", onupdate="RESTRICT"),
        sa.ForeignKeyConstraint(["round_id"], ["interview_rounds.id"], ondelete="CASCADE", onupdate="RESTRICT"),
        sa.ForeignKeyConstraint(["scheduled_by_id"], ["members.id"], ondelete="SET NULL", onupdate="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "application_status_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("changed_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("changed_by_name", sa.String(), nullable=True),
        sa.Column("changed_by_email", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE", onupdate="RESTRICT"),
        sa.ForeignKeyConstraint(["changed_by_id"], ["members.id"], ondelete="SET NULL", onupdate="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("application_status_history")
    op.drop_table("interviews")
    op.drop_table("availability_requests")
    op.drop_table("member_panels")
    op.drop_table("reports")
    op.drop_table("applications")
    op.drop_table("dashboard_stats")
    op.drop_table("panels")
    op.drop_table("members")
    op.drop_table("interview_rounds")
    op.drop_table("job_descriptions")
    op.drop_table("resumes")
