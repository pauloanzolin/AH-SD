from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectOut(ProjectBase):
    id: int
    created_at: datetime
    status: str
    participant_count: Optional[int] = 0
    session_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)

class ParticipantBase(BaseModel):
    name: str
    age: Optional[int] = None
    education_level: Optional[str] = None
    notes: Optional[str] = None

class ParticipantCreate(ParticipantBase):
    pass

class ParticipantOut(ParticipantBase):
    id: int
    project_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TestSessionCreate(BaseModel):
    participant_name: str
    age: Optional[int] = None
    education_level: Optional[str] = None
    notes: Optional[str] = None

class TestSessionOut(BaseModel):
    id: int
    project_id: int
    participant_id: int
    participant_name: Optional[str] = None
    status: str
    current_module: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: float
    results_summary: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

class ResponseItem(BaseModel):
    item_id: str
    user_answer: Any
    reaction_time_ms: float
    raw_data: Optional[Dict[str, Any]] = None

class ModuleSubmitRequest(BaseModel):
    responses: List[ResponseItem]
    telemetry: Optional[Dict[str, Any]] = None

class SessionCompleteRequest(BaseModel):
    notes: Optional[str] = None
