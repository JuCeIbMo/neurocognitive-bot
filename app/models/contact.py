from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class UserType(StrEnum):
    LEAD = "lead"
    STUDENT = "student"
    PATIENT = "patient"
    UNKNOWN = "unknown"


class LeadPhase(StrEnum):
    DISCOVERY = "discovery"
    PAIN = "pain"
    GAP = "gap"
    SOLUTION = "solution"
    CLOSING = "closing"
    FOLLOWUP = "followup"
    REDIRECT = "redirect"


class StudentPhase(StrEnum):
    IDENTIFY_ISSUE = "identify_issue"
    PROVIDE_INFO = "provide_info"
    ESCALATE = "escalate"


class PatientPhase(StrEnum):
    EMPATHIZE = "empathize"
    PRESENT_CLINIC = "present_clinic"
    COLLECT_INFO = "collect_info"
    NOTIFY_STAFF = "notify_staff"


class Contact(BaseModel):
    kommo_contact_id: str
    user_type: UserType = UserType.UNKNOWN
    name: str | None = None
    profession: str | None = None
    is_eligible: bool | None = None
    phase: str = "initial"
    program: str | None = None
    collected_info: dict = Field(default_factory=dict)
    last_message_at: datetime | None = None
