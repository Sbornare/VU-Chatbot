from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    industry = Column(String)
    location = Column(String)
    website = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    hr_contact = Column(String, nullable=True)
    hr_email = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    placements = relationship("Placement", back_populates="company")
    job_openings = relationship("JobOpening", back_populates="company")


class JobOpening(Base):
    __tablename__ = "job_openings"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    title = Column(String, index=True)
    description = Column(Text)
    requirements = Column(Text)
    package_min = Column(Float, nullable=True)  # in LPA
    package_max = Column(Float, nullable=True)  # in LPA
    location = Column(String)
    job_type = Column(String)  # Full-time, Internship, etc.
    eligibility_criteria = Column(Text)
    application_deadline = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="job_openings")
    placements = relationship("Placement", back_populates="job_opening")


class Placement(Base):
    __tablename__ = "placements"

    id = Column(Integer, primary_key=True, index=True)
    student_name = Column(String, index=True)
    student_email = Column(String, nullable=True)
    student_id = Column(String, nullable=True)  # University student ID
    program = Column(String)  # B.Tech CSE, MBA, etc.
    graduation_year = Column(Integer)
    cgpa = Column(Float, nullable=True)
    
    # Company and job details
    company_id = Column(Integer, ForeignKey("companies.id"))
    job_opening_id = Column(Integer, ForeignKey("job_openings.id"), nullable=True)
    job_title = Column(String)
    package = Column(Float)  # in LPA
    job_location = Column(String)
    
    # Selection process details
    selection_rounds = Column(Text, nullable=True)  # JSON or text description
    interview_tips = Column(Text, nullable=True)
    preparation_resources = Column(Text, nullable=True)
    
    # Timeline
    application_date = Column(DateTime, nullable=True)
    selection_date = Column(DateTime, nullable=True)
    joining_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="placements")
    job_opening = relationship("JobOpening", back_populates="placements")


class PlacementStats(Base):
    __tablename__ = "placement_stats"

    id = Column(Integer, primary_key=True, index=True)
    academic_year = Column(String)  # 2023-24
    program = Column(String)  # B.Tech CSE, MBA, etc.
    total_students = Column(Integer)
    placed_students = Column(Integer)
    placement_percentage = Column(Float)
    average_package = Column(Float)
    highest_package = Column(Float)
    top_recruiters = Column(Text)  # JSON list of company names
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)