"""
Pydantic models — the contract between frontend, backend, and the LLM.
Keeping these strict is what makes the itinerary cards / chat UI render
reliably instead of you parsing free-text LLM output by hand.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


# ---------- Negotiation ----------

class ChatMessage(BaseModel):
    sender: str
    text: str


class NegotiateRequest(BaseModel):
    trip_name: str
    participants: List[str]
    messages: List[ChatMessage]
    budget_pp: Optional[int] = None  # optional hard cap in INR


class ItineraryOption(BaseModel):
    id: str                 # "option_1", "option_2", "option_3"
    tag: str                # "OPTION 1", "RECOMMENDED", etc.
    title: str               # "Comfort First"
    hotel: str
    food: str
    activities: str
    budget_pp: int
    matches: List[str]       # which participants' priorities this best satisfies


class Conflict(BaseModel):
    between: List[str]       # participant names in conflict
    description: str


class NegotiateResponse(BaseModel):
    detected_priorities: dict            # {"Shreya": "Michelin dining priority", ...}
    conflicts: List[Conflict]
    options: List[ItineraryOption]
    recommended_option_id: str
    ai_message: str                      # the quoted "I understand everyone's..." line


# ---------- Disruption / Replanning ----------

class DisruptionRequest(BaseModel):
    trip_name: str
    current_option_id: str
    disruption_type: str     # "hotel_cancelled" | "flight_delayed" | "weather_alert"
    affected_item: str       # e.g. hotel name that got cancelled


class Alternative(BaseModel):
    name: str
    budget_delta_pct: float   # +5.0 means 5% over original budget
    reason: str


class VerificationCheck(BaseModel):
    label: str
    passed: bool


class ReplanResponse(BaseModel):
    alert_message: str
    ai_explanation: str
    alternatives: List[Alternative]
    verification: List[VerificationCheck]
