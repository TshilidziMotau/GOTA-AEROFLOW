from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, JSON, Float, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default='analyst')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Project(Base):
    __tablename__ = 'projects'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    site_name: Mapped[str] = mapped_column(String(200))
    site_type: Mapped[str] = mapped_column(String(50))
    location: Mapped[str] = mapped_column(String(255))
    survey_date: Mapped[str] = mapped_column(String(50))
    survey_period: Mapped[str] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Video(Base):
    __tablename__ = 'videos'
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'))
    filename: Mapped[str] = mapped_column(String(255))
    path: Mapped[str] = mapped_column(String(500))
    duration_s: Mapped[float | None] = mapped_column(Float, nullable=True)
    fps: Mapped[float | None] = mapped_column(Float, nullable=True)
    resolution: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SceneDefinition(Base):
    __tablename__ = 'scene_definitions'
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'))
    config: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AnalysisRun(Base):
    __tablename__ = 'analysis_runs'
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'))
    status: Mapped[str] = mapped_column(String(30), default='queued')
    stage: Mapped[str] = mapped_column(String(50), default='queued')
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ManualEdit(Base):
    __tablename__ = 'manual_edits'
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    edit_type: Mapped[str] = mapped_column(String(100))
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EvidenceExport(Base):
    __tablename__ = 'exports'
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'))
    export_type: Mapped[str] = mapped_column(String(20))
    path: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Report(Base):
    __tablename__ = 'reports'
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'))
    status: Mapped[str] = mapped_column(String(20), default='generated')
    path: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
