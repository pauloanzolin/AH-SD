from datetime import datetime
import json
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="active")

    participants = relationship("Participant", back_populates="project", cascade="all, delete-orphan")
    sessions = relationship("TestSession", back_populates="project", cascade="all, delete-orphan")

class Participant(Base):
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    age = Column(Integer, nullable=True)
    education_level = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="participants")
    sessions = relationship("TestSession", back_populates="participant", cascade="all, delete-orphan")

class TestSession(Base):
    __tablename__ = "test_sessions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    participant_id = Column(Integer, ForeignKey("participants.id"), nullable=False)
    status = Column(String(50), default="not_started") # not_started, in_progress, completed
    current_module = Column(String(100), default="fenomenologico")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, default=0.0)
    
    # Telemetria de validade (perda de foco, blur, cliques impossíveis <150ms)
    validity_data = Column(Text, default="{}") 
    
    # Resumo psicométrico calculado (z-scores, percentis, QI estimado, radar, interpretação)
    results_summary = Column(Text, nullable=True)

    project = relationship("Project", back_populates="sessions")
    participant = relationship("Participant", back_populates="sessions")
    responses = relationship("TestResponse", back_populates="session", cascade="all, delete-orphan")

    def get_validity_data(self):
        try:
            return json.loads(self.validity_data) if self.validity_data else {}
        except Exception:
            return {}

    def set_validity_data(self, data):
        self.validity_data = json.dumps(data, ensure_ascii=False)

    def get_results_summary(self):
        try:
            return json.loads(self.results_summary) if self.results_summary else None
        except Exception:
            return None

    def set_results_summary(self, data):
        self.results_summary = json.dumps(data, ensure_ascii=False)

class TestResponse(Base):
    __tablename__ = "test_responses"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("test_sessions.id"), nullable=False)
    module_name = Column(String(100), nullable=False)
    item_id = Column(String(100), nullable=False)
    user_answer = Column(Text, nullable=True)
    reaction_time_ms = Column(Float, default=0.0)
    is_correct = Column(Boolean, nullable=True)
    raw_data = Column(Text, nullable=True) # Dados contextuais adicionais em JSON
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("TestSession", back_populates="responses")
