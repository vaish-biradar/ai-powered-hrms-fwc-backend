from sqlmodel import SQLModel, Field, create_engine, Session, select, Relationship
import os
from dotenv import load_dotenv
from typing import Optional, List
import datetime
from sqlalchemy import Column, String, Text, ForeignKey, update, Integer, Boolean, Float, Date, UniqueConstraint
from urllib.parse import quote_plus
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSONB
load_dotenv()

# Database Models
class Resume(SQLModel, table=True):
    __tablename__ = "resumes"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(UUID(as_uuid=True), primary_key=True))
    name: str
    email: str = Field(sa_column=Column(String, unique=True))
    phone: Optional[str] = None
    summary: Optional[str] = None
    experience_status: Optional[str] = None
    years_of_experience: Optional[str] = None
    suitable_roles: List[str] = Field(sa_column=Column(JSONB))
    path: str
    text: str = Field(sa_column=Column(Text))
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)

    applications: List["Application"] = Relationship(back_populates="resume")
    reports: List["Report"] = Relationship(back_populates="resume")



class JobDescription(SQLModel, table=True):
    __tablename__ = "job_descriptions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(UUID(as_uuid=True), primary_key=True))
    title: str
    text: Optional[str] = None
    department: Optional[str] = None
    employment_type: Optional[str] = None
    location: Optional[str] = None
    experience_level: Optional[str] = None
    summary: Optional[str] = None
    skills: Optional[str] = None
    description: str = Field(sa_column=Column(Text))
    path: Optional[str] = None
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    status: Optional[str] = "Open"
    total_openings: int = 0
    occupied_openings: int = 0
    submitted_by: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSONB)  # Use JSONB if needed: from sqlalchemy.dialects.postgresql import JSONB
    )
    applications: List["Application"] = Relationship(back_populates="job_description")
    reports: List["Report"] = Relationship(back_populates="job_description")



class Report(SQLModel, table=True):
    __tablename__ = "reports"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(UUID(as_uuid=True), primary_key=True))
    resume_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="RESTRICT", onupdate="RESTRICT"))
    )
    job_description_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("job_descriptions.id", ondelete="RESTRICT", onupdate="RESTRICT"))
    )
    content: dict = Field(sa_column=Column(JSONB))
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)

    resume: Optional[Resume] = Relationship(back_populates="reports")
    job_description: Optional[JobDescription] = Relationship(back_populates="reports")



class Application(SQLModel, table=True):
    __tablename__ = "applications"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(UUID(as_uuid=True), primary_key=True))
    resume_id: Optional[uuid.UUID] = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="RESTRICT", onupdate="RESTRICT"),nullable=True)
    )
    job_description_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("job_descriptions.id", ondelete="RESTRICT", onupdate="RESTRICT"))
    )
   

    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    candidate_phone: Optional[str] = None
    total_experience: Optional[str] = None
    current_ctc: Optional[str] = None
    expected_ctc: Optional[str] = None
    current_company: Optional[str] = None
    current_location: Optional[str] = None
    current_job_title: Optional[str] = None
    notice_period: Optional[str] = None
    resume_url: Optional[str] = None
    job_title: Optional[str] = None
    jd_url: Optional[str] = None
    report_url: Optional[str] = None
    suitable_roles: Optional[List[str]] = Field(default_factory=list, sa_column=Column(JSONB))
    similarity: Optional[float] = None
    source: Optional[str] = None
    status: str
    current_round_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(UUID(as_uuid=True), ForeignKey("interview_rounds.id", ondelete="SET NULL", onupdate="RESTRICT"), nullable=True),
    )
    applied_date: Optional[datetime.datetime] = None
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)

    # Relationships
    resume: Optional["Resume"] = Relationship(back_populates="applications")
    job_description: Optional["JobDescription"] = Relationship(back_populates="applications")


class InterviewRound(SQLModel, table=True):
    __tablename__ = "interview_rounds"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(UUID(as_uuid=True), primary_key=True))
    round_name: str
    description: Optional[str] = None
    round_order: int = Field(default=1, sa_column=Column(Integer, nullable=False, default=1))
    is_active: bool = Field(default=True, sa_column=Column(Boolean, nullable=False, default=True))
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)


class Member(SQLModel, table=True):
    __tablename__ = "members"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(UUID(as_uuid=True), primary_key=True))
    name: str
    email: str = Field(sa_column=Column(String, unique=True, nullable=False))
    department: Optional[str] = None
    role: Optional[str] = None
    expertise: Optional[str] = None
    invitation_token: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True))
    invitation_status: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True))
    invitation_expiry: Optional[datetime.datetime] = None
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)


class Panel(SQLModel, table=True):
    __tablename__ = "panels"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(UUID(as_uuid=True), primary_key=True))
    panel_name: str
    department: Optional[str] = None
    positions: Optional[str] = None
    interviews_completed: int = Field(default=0, sa_column=Column(Integer, nullable=False, default=0))
    status: str = Field(default="active")
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)


class MemberPanel(SQLModel, table=True):
    __tablename__ = "member_panels"

    member_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("members.id", ondelete="CASCADE", onupdate="RESTRICT"), primary_key=True)
    )
    panel_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("panels.id", ondelete="CASCADE", onupdate="RESTRICT"), primary_key=True)
    )


class DashboardStat(SQLModel, table=True):
    __tablename__ = "dashboard_stats"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(UUID(as_uuid=True), primary_key=True))
    month_year: Optional[str] = None
    resumes: int = 0
    job_descriptions: int = 0
    applications: int = 0
    hired: int = 0
    applied_date: Optional[datetime.datetime] = None
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)


class AvailabilityRequest(SQLModel, table=True):
    __tablename__ = "availability_requests"

    token: str = Field(sa_column=Column(String, primary_key=True))
    member_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("members.id", ondelete="CASCADE", onupdate="RESTRICT"), nullable=False)
    )
    application_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE", onupdate="RESTRICT"), nullable=False)
    )
    round_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("interview_rounds.id", ondelete="CASCADE", onupdate="RESTRICT"), nullable=False)
    )
    requested_date: Optional[datetime.datetime] = None
    requested_by_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(UUID(as_uuid=True), ForeignKey("members.id", ondelete="SET NULL", onupdate="RESTRICT"), nullable=True),
    )
    expires_at: Optional[datetime.datetime] = None
    response: Optional[str] = None
    responded_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)


class Interview(SQLModel, table=True):
    __tablename__ = "interviews"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(UUID(as_uuid=True), primary_key=True))
    application_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE", onupdate="RESTRICT"), nullable=False)
    )
    round_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("interview_rounds.id", ondelete="CASCADE", onupdate="RESTRICT"), nullable=False)
    )
    panel_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(UUID(as_uuid=True), ForeignKey("panels.id", ondelete="SET NULL", onupdate="RESTRICT"), nullable=True),
    )
    scheduled_by_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(UUID(as_uuid=True), ForeignKey("members.id", ondelete="SET NULL", onupdate="RESTRICT"), nullable=True),
    )
    scheduled_date: Optional[datetime.datetime] = None
    meeting_link: Optional[str] = None
    meeting_location: Optional[str] = None
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)


class ApplicationStatusHistory(SQLModel, table=True):
    __tablename__ = "application_status_history"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(UUID(as_uuid=True), primary_key=True))
    application_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE", onupdate="RESTRICT"), nullable=False)
    )
    status: str
    feedback: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    changed_by_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(UUID(as_uuid=True), ForeignKey("members.id", ondelete="SET NULL", onupdate="RESTRICT"), nullable=True),
    )
    changed_by_name: Optional[str] = None
    changed_by_email: Optional[str] = None
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)


class Employee(SQLModel, table=True):
    __tablename__ = "employees"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(UUID(as_uuid=True), primary_key=True))
    employee_code: str = Field(sa_column=Column(String, unique=True, nullable=False))
    first_name: str
    last_name: str
    email: str = Field(sa_column=Column(String, unique=True, nullable=False))
    phone: Optional[str] = None
    department: str
    designation: str
    employment_type: str = Field(default="Full-time")
    date_of_joining: datetime.date = Field(sa_column=Column(Date, nullable=False))
    manager_name: Optional[str] = None
    base_salary: float = Field(default=0.0, sa_column=Column(Float, nullable=False, default=0.0))
    status: str = Field(default="Active")
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)


class AttendanceRecord(SQLModel, table=True):
    __tablename__ = "attendance_records"
    __table_args__ = (UniqueConstraint("employee_id", "attendance_date", name="uq_attendance_employee_date"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(UUID(as_uuid=True), primary_key=True))
    employee_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE", onupdate="RESTRICT"), nullable=False)
    )
    attendance_date: datetime.date = Field(sa_column=Column(Date, nullable=False))
    check_in: Optional[datetime.datetime] = None
    check_out: Optional[datetime.datetime] = None
    status: str = Field(default="Present")
    work_mode: Optional[str] = None
    notes: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)


class PayrollRecord(SQLModel, table=True):
    __tablename__ = "payroll_records"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(UUID(as_uuid=True), primary_key=True))
    employee_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE", onupdate="RESTRICT"), nullable=False)
    )
    pay_period_start: datetime.date = Field(sa_column=Column(Date, nullable=False))
    pay_period_end: datetime.date = Field(sa_column=Column(Date, nullable=False))
    gross_salary: float = Field(default=0.0, sa_column=Column(Float, nullable=False, default=0.0))
    deductions: float = Field(default=0.0, sa_column=Column(Float, nullable=False, default=0.0))
    bonuses: float = Field(default=0.0, sa_column=Column(Float, nullable=False, default=0.0))
    net_salary: float = Field(default=0.0, sa_column=Column(Float, nullable=False, default=0.0))
    status: str = Field(default="Pending")
    paid_on: Optional[datetime.datetime] = None
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)


class PerformanceReview(SQLModel, table=True):
    __tablename__ = "performance_reviews"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(UUID(as_uuid=True), primary_key=True))
    employee_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE", onupdate="RESTRICT"), nullable=False)
    )
    review_cycle: str
    reviewer_name: str
    goals: Optional[List[str]] = Field(default_factory=list, sa_column=Column(JSONB))
    rating: Optional[float] = Field(default=None, sa_column=Column(Float, nullable=True))
    feedback: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    strengths: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    improvements: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    review_date: datetime.date = Field(sa_column=Column(Date, nullable=False))
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)


class MockInterview(SQLModel, table=True):
    __tablename__ = "mock_interviews"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(UUID(as_uuid=True), primary_key=True))
    resume_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="SET NULL", onupdate="RESTRICT"), nullable=True),
    )
    job_description_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("job_descriptions.id", ondelete="CASCADE", onupdate="RESTRICT"), nullable=False)
    )
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    transcript_text: str = Field(sa_column=Column(Text, nullable=False))
    conversation: list = Field(default_factory=list, sa_column=Column(JSONB, nullable=False))
    status: str = Field(default="completed")
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)


class PostgresDB:
    def __init__(self, connection_string):
        # Create engine with connection health checks and SSL required for managed DBs
        # Use pool_pre_ping to avoid "server has gone away"/closed connection errors
        # and pool_recycle to retire very old connections.
        retries = 3
        for attempt in range(1, retries + 1):
            try:
                self.engine = create_engine(
                    connection_string,
                    pool_pre_ping=True,
                    pool_recycle=1800,
                    connect_args={"sslmode": "require"},
                )
                break
            except Exception:
                if attempt == retries:
                    raise
        self.create_tables()
        
    def create_tables(self):
        """Creates all tables defined by SQLModel classes"""
        SQLModel.metadata.create_all(self.engine)
        
    def insert(self, collection, document):
        """Inserts or updates a document in the specified collection"""
        with Session(self.engine) as session:
            model_mapping = {
                "resumes": Resume,
                "jds": JobDescription,
                "reports": Report,
                "applications": Application,
                "employees": Employee,
                "attendance_records": AttendanceRecord,
                "payroll_records": PayrollRecord,
                "performance_reviews": PerformanceReview,
                "mock_interviews": MockInterview,
            }
            
            if collection not in model_mapping:
                raise ValueError(f"Invalid collection: {collection}")
                
            model_class = model_mapping[collection]
            
            # Check if record exists by primary id
            existing = None
            if document.get("id"):
                existing = session.get(model_class, document["id"])

            if existing:
                # Update existing record
                for key, value in document.items():
                    setattr(existing, key, value)
            else:
                # Create new record
                new_record = model_class(**document)
                session.add(new_record)
                
            session.commit()
    
    def get(self, collection, doc_id):
        """Retrieves a document by ID from the specified collection"""
        with Session(self.engine) as session:
            model_mapping = {
                "resumes": Resume,
                "jds": JobDescription,
                "reports": Report,
                "applications": Application,
                "employees": Employee,
                "attendance_records": AttendanceRecord,
                "payroll_records": PayrollRecord,
                "performance_reviews": PerformanceReview,
                "mock_interviews": MockInterview,
            }
            
            if collection not in model_mapping:
                raise ValueError(f"Invalid collection: {collection}")
                
            model_class = model_mapping[collection]
            record = session.get(model_class, doc_id)
            
            if record:
                # Convert SQLModel object to dictionary
                return {column.name: getattr(record, column.name) 
                        for column in model_class.__table__.columns}
            return None
    
    def get_all(self, collection):
        """Retrieves all documents from the specified collection"""
        with Session(self.engine) as session:
            model_mapping = {
                "resumes": Resume,
                "jds": JobDescription,
                "reports": Report,
                "applications": Application,
                "employees": Employee,
                "attendance_records": AttendanceRecord,
                "payroll_records": PayrollRecord,
                "performance_reviews": PerformanceReview,
                "mock_interviews": MockInterview,
            }
            
            if collection not in model_mapping:
                raise ValueError(f"Invalid collection: {collection}")
                
            model_class = model_mapping[collection]
            statement = select(model_class)
            results = session.exec(statement).all()
            
            # Convert SQLModel objects to dictionaries
            return [{column.name: getattr(record, column.name) 
                    for column in model_class.__table__.columns}
                    for record in results]
    
    def find_one(self, collection, query):
        """Retrieves a single document based on the given query"""
        with Session(self.engine) as session:
            model_mapping = {
                "resumes": Resume,
                "jds": JobDescription,
                "reports": Report,
                "applications": Application,
                "employees": Employee,
                "attendance_records": AttendanceRecord,
                "payroll_records": PayrollRecord,
                "performance_reviews": PerformanceReview,
                "mock_interviews": MockInterview,
            }
            
            if collection not in model_mapping:
                raise ValueError(f"Invalid collection: {collection}")
                
            model_class = model_mapping[collection]
            
            # Build query
            statement = select(model_class)
            for key, value in query.items():
                statement = statement.where(getattr(model_class, key) == value)
                
            result = session.exec(statement).first()
            
            if result:
                # Convert SQLModel object to dictionary
                return {column.name: getattr(result, column.name) 
                        for column in model_class.__table__.columns}
            return None
    
    def delete(self, collection, doc_id):
        """Deletes a document by ID from the specified collection"""
        with Session(self.engine) as session:
            model_mapping = {
                "resumes": Resume,
                "jds": JobDescription,
                "reports": Report,
                "applications": Application,
                "employees": Employee,
                "attendance_records": AttendanceRecord,
                "payroll_records": PayrollRecord,
                "performance_reviews": PerformanceReview,
                "mock_interviews": MockInterview,
            }
            
            if collection not in model_mapping:
                raise ValueError(f"Invalid collection: {collection}")
                
            model_class = model_mapping[collection]
            record = session.get(model_class, doc_id)
            
            if record:
                session.delete(record)
                session.commit()
                return True
            return False
    
    def clear_db(self, collection=None):
        """Deletes all documents from a specific collection or all collections"""
        with Session(self.engine) as session:
            model_mapping = {
                "resumes": Resume,
                "jds": JobDescription,
                "reports": Report,
                "applications": Application,
                "employees": Employee,
                "attendance_records": AttendanceRecord,
                "payroll_records": PayrollRecord,
                "performance_reviews": PerformanceReview,
                "mock_interviews": MockInterview,
            }
            
            if collection:
                if collection not in model_mapping:
                    raise ValueError(f"Collection '{collection}' does not exist.")
                model_class = model_mapping[collection]
                statement = select(model_class)
                records = session.exec(statement).all()
                
                for record in records:
                    session.delete(record)
            else:
                for collection_name, model_class in model_mapping.items():
                    statement = select(model_class)
                    records = session.exec(statement).all()
                    
                    for record in records:
                        session.delete(record)
                        
            session.commit()
    
    def update(self, collection, doc_id, updates):
        """Updates specific fields in a document"""
        with Session(self.engine) as session:
            model_mapping = {
                "resumes": Resume,
                "jds": JobDescription,
                "reports": Report,
                "applications": Application,
                "employees": Employee,
                "attendance_records": AttendanceRecord,
                "payroll_records": PayrollRecord,
                "performance_reviews": PerformanceReview,
            }
            
            if collection not in model_mapping:
                raise ValueError(f"Invalid collection: {collection}")
                
            model_class = model_mapping[collection]
            record = session.get(model_class, doc_id)
            
            if not record:
                raise ValueError("Document not found.")
                
            for key, value in updates.items():
                setattr(record, key, value)
                
                session.commit()
    def update_many(self, collection, filter_conditions, updates):
        """Updates multiple records based on filter conditions."""
        with Session(self.engine) as session:
            model_mapping = {
                "resumes": Resume,
                "jds": JobDescription,
                "reports": Report,
                "applications": Application
            }

            if collection not in model_mapping:
                raise ValueError(f"Invalid collection: {collection}")

            model_class = model_mapping[collection]

            # Prepare the filter conditions as SQLAlchemy expressions
            filter_expression = filter_conditions

            # Prepare the update statement
            statement = update(model_class).where(filter_expression).values(updates)

            # Execute the update
            session.execute(statement)
            session.commit()


def build_database_url() -> str:
    db_user = os.getenv("DB_USER", "dohr_postgres")
    db_password = os.getenv("DB_PASSWORD", "")
    db_host = os.getenv("DB_HOST", "hr-recruitment-postgres.postgres.database.azure.com")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "DOHR_Recruitment")

    if not db_password:
        raise ValueError("DB_PASSWORD environment variable is not set. Please configure your .env file.")

    encoded_password = quote_plus(db_password)
    return f"postgresql://{db_user}:{encoded_password}@{db_host}:{db_port}/{db_name}"


db = None
if os.getenv("SKIP_DB_INIT", "0") != "1":
    try:
        DATABASE_URL = build_database_url()
        db = PostgresDB(DATABASE_URL)
        print("Database connection successful!")
    except Exception as e:
        print(f"Database connection error: {str(e)}")
