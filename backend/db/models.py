from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean
)
from sqlalchemy.orm import relationship

from backend.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    projects = relationship("Project", back_populates="user")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    status = Column(String(50), default="draft")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User", back_populates="projects")
    optimisation_runs = relationship("OptimisationRun", back_populates="project")
    quotes = relationship("Quote", back_populates="project")
    reports = relationship("Report", back_populates="project")


class PanelType(Base):
    __tablename__ = "panel_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    width_mm = Column(Integer, nullable=False)
    height_mm = Column(Integer, nullable=False)
    thickness_mm = Column(Integer, nullable=False)
    material = Column(String(255), nullable=False)
    cost_per_unit = Column(Float, nullable=False)

    optimisation_runs = relationship("OptimisationRun", back_populates="panel_type")


class OptimisationRun(Base):
    __tablename__ = "optimisation_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    panel_type_id = Column(Integer, ForeignKey("panel_types.id"), nullable=False)
    wall_width_mm = Column(Integer, nullable=False)
    wall_height_mm = Column(Integer, nullable=False)
    status = Column(String(50), default="pending")
    result_json = Column(Text, nullable=True)
    waste_percentage = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    project = relationship("Project", back_populates="optimisation_runs")
    panel_type = relationship("PanelType", back_populates="optimisation_runs")


class Quote(Base):
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    optimisation_run_id = Column(Integer, ForeignKey("optimisation_runs.id"), nullable=True)
    ai_summary = Column(Text, nullable=False)
    total_cost = Column(Float, nullable=False)
    breakdown_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    project = relationship("Project", back_populates="quotes")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    content_markdown = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    project = relationship("Project", back_populates="reports")
