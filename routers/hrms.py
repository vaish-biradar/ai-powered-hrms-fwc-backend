from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from sqlmodel import Session, select
from sqlalchemy import func

from utils.database import (
    db,
    Employee,
    AttendanceRecord,
    PayrollRecord,
    PerformanceReview,
)


hrms = APIRouter(prefix="/hrms", tags=["HRMS"])


class EmployeeCreate(BaseModel):
    employee_code: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    department: str
    designation: str
    employment_type: str = "Full-time"
    date_of_joining: date
    manager_name: Optional[str] = None
    base_salary: float = 0.0
    status: str = "Active"


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    employment_type: Optional[str] = None
    date_of_joining: Optional[date] = None
    manager_name: Optional[str] = None
    base_salary: Optional[float] = None
    status: Optional[str] = None


class AttendanceUpsert(BaseModel):
    employee_id: UUID
    attendance_date: date
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    status: str = "Present"
    work_mode: Optional[str] = None
    notes: Optional[str] = None


class PayrollCreate(BaseModel):
    employee_id: UUID
    pay_period_start: date
    pay_period_end: date
    gross_salary: float = 0.0
    deductions: float = 0.0
    bonuses: float = 0.0
    net_salary: Optional[float] = None
    status: str = "Pending"


class PayrollMarkPaid(BaseModel):
    paid_on: Optional[datetime] = None


class PerformanceCreate(BaseModel):
    employee_id: UUID
    review_cycle: str
    reviewer_name: str
    goals: List[str] = Field(default_factory=list)
    rating: Optional[float] = None
    feedback: Optional[str] = None
    strengths: Optional[str] = None
    improvements: Optional[str] = None
    review_date: date


def _engine():
    if db is None or db.engine is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return db.engine


@hrms.post("/employees")
def create_employee(payload: EmployeeCreate):
    with Session(_engine()) as session:
        existing_email = session.exec(select(Employee).where(Employee.email == payload.email)).first()
        if existing_email:
            raise HTTPException(status_code=409, detail="Employee with this email already exists")

        existing_code = session.exec(select(Employee).where(Employee.employee_code == payload.employee_code)).first()
        if existing_code:
            raise HTTPException(status_code=409, detail="Employee code already exists")

        employee = Employee(**payload.model_dump())
        session.add(employee)
        session.commit()
        session.refresh(employee)
        return jsonable_encoder(employee)


@hrms.get("/employees")
def list_employees(
    department: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
):
    with Session(_engine()) as session:
        statement = select(Employee)

        if department:
            statement = statement.where(Employee.department == department)
        if status:
            statement = statement.where(Employee.status == status)
        if search:
            pattern = f"%{search.lower()}%"
            statement = statement.where(
                func.lower(Employee.first_name + " " + Employee.last_name).like(pattern)
                | func.lower(Employee.email).like(pattern)
                | func.lower(Employee.employee_code).like(pattern)
            )

        employees = session.exec(statement.order_by(Employee.created_at.desc())).all()
        return jsonable_encoder(employees)


@hrms.get("/employees/{employee_id}")
def get_employee(employee_id: UUID):
    with Session(_engine()) as session:
        employee = session.get(Employee, employee_id)
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        return jsonable_encoder(employee)


@hrms.put("/employees/{employee_id}")
def update_employee(employee_id: UUID, payload: EmployeeUpdate):
    with Session(_engine()) as session:
        employee = session.get(Employee, employee_id)
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        updates = payload.model_dump(exclude_unset=True)

        if "email" in updates and updates["email"] != employee.email:
            existing_email = session.exec(select(Employee).where(Employee.email == updates["email"])).first()
            if existing_email:
                raise HTTPException(status_code=409, detail="Employee with this email already exists")

        for key, value in updates.items():
            setattr(employee, key, value)

        employee.updated_at = datetime.now()
        session.add(employee)
        session.commit()
        session.refresh(employee)
        return jsonable_encoder(employee)


@hrms.post("/attendance")
def upsert_attendance(payload: AttendanceUpsert):
    with Session(_engine()) as session:
        employee = session.get(Employee, payload.employee_id)
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        existing = session.exec(
            select(AttendanceRecord).where(
                AttendanceRecord.employee_id == payload.employee_id,
                AttendanceRecord.attendance_date == payload.attendance_date,
            )
        ).first()

        if existing:
            existing.check_in = payload.check_in
            existing.check_out = payload.check_out
            existing.status = payload.status
            existing.work_mode = payload.work_mode
            existing.notes = payload.notes
            session.add(existing)
            session.commit()
            session.refresh(existing)
            return jsonable_encoder(existing)

        record = AttendanceRecord(**payload.model_dump())
        session.add(record)
        session.commit()
        session.refresh(record)
        return jsonable_encoder(record)


@hrms.get("/attendance")
def list_attendance(
    employee_id: Optional[UUID] = Query(default=None),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
):
    with Session(_engine()) as session:
        statement = select(AttendanceRecord)

        if employee_id:
            statement = statement.where(AttendanceRecord.employee_id == employee_id)
        if start_date:
            statement = statement.where(AttendanceRecord.attendance_date >= start_date)
        if end_date:
            statement = statement.where(AttendanceRecord.attendance_date <= end_date)

        rows = session.exec(statement.order_by(AttendanceRecord.attendance_date.desc())).all()
        return jsonable_encoder(rows)


@hrms.post("/payroll")
def create_payroll_record(payload: PayrollCreate):
    with Session(_engine()) as session:
        employee = session.get(Employee, payload.employee_id)
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        net_salary = payload.net_salary
        if net_salary is None:
            net_salary = payload.gross_salary + payload.bonuses - payload.deductions

        record = PayrollRecord(
            employee_id=payload.employee_id,
            pay_period_start=payload.pay_period_start,
            pay_period_end=payload.pay_period_end,
            gross_salary=payload.gross_salary,
            deductions=payload.deductions,
            bonuses=payload.bonuses,
            net_salary=net_salary,
            status=payload.status,
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return jsonable_encoder(record)


@hrms.get("/payroll")
def list_payroll(employee_id: Optional[UUID] = Query(default=None)):
    with Session(_engine()) as session:
        statement = select(PayrollRecord)
        if employee_id:
            statement = statement.where(PayrollRecord.employee_id == employee_id)
        rows = session.exec(statement.order_by(PayrollRecord.created_at.desc())).all()
        return jsonable_encoder(rows)


@hrms.put("/payroll/{payroll_id}/mark-paid")
def mark_payroll_as_paid(payroll_id: UUID, payload: PayrollMarkPaid):
    with Session(_engine()) as session:
        record = session.get(PayrollRecord, payroll_id)
        if not record:
            raise HTTPException(status_code=404, detail="Payroll record not found")

        record.status = "Paid"
        record.paid_on = payload.paid_on or datetime.now()
        session.add(record)
        session.commit()
        session.refresh(record)
        return jsonable_encoder(record)


@hrms.post("/performance")
def create_performance_review(payload: PerformanceCreate):
    with Session(_engine()) as session:
        employee = session.get(Employee, payload.employee_id)
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        review = PerformanceReview(**payload.model_dump())
        session.add(review)
        session.commit()
        session.refresh(review)
        return jsonable_encoder(review)


@hrms.get("/performance")
def list_performance_reviews(
    employee_id: Optional[UUID] = Query(default=None),
    review_cycle: Optional[str] = Query(default=None),
):
    with Session(_engine()) as session:
        statement = select(PerformanceReview)
        if employee_id:
            statement = statement.where(PerformanceReview.employee_id == employee_id)
        if review_cycle:
            statement = statement.where(PerformanceReview.review_cycle == review_cycle)

        rows = session.exec(statement.order_by(PerformanceReview.review_date.desc())).all()
        return jsonable_encoder(rows)


@hrms.get("/overview")
def hrms_overview():
    with Session(_engine()) as session:
        active_employees = session.exec(
            select(func.count()).select_from(Employee).where(Employee.status == "Active")
        ).one()
        attendance_today = session.exec(
            select(func.count()).select_from(AttendanceRecord).where(AttendanceRecord.attendance_date == date.today())
        ).one()
        pending_payroll = session.exec(
            select(func.count()).select_from(PayrollRecord).where(PayrollRecord.status == "Pending")
        ).one()
        avg_rating = session.exec(select(func.avg(PerformanceReview.rating))).one()

        return {
            "active_employees": int(active_employees or 0),
            "attendance_marked_today": int(attendance_today or 0),
            "pending_payroll_records": int(pending_payroll or 0),
            "average_performance_rating": round(float(avg_rating), 2) if avg_rating is not None else None,
        }
