"""
Travex agent core.

Two entry points:
  - negotiate(...)  -> reads the group chat, detects conflicts, proposes 3 options
  - replan(...)      -> reacts to a disruption, proposes alternatives

Both force the model to respond through a tool_use block matching an exact
JSON schema, so you never have to regex-parse free text out of a chat reply.
This is the single most important trick for a hackathon: don't trust the
model to "please respond only in JSON" — force it with a tool definition.
"""
import os
import json
from anthropic import Anthropic
from dotenv import load_dotenv

from .schemas import NegotiateRequest, NegotiateResponse, DisruptionRequest, ReplanResponse

load_dotenv()

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-5"

DATA_DIR = os.path.join(os.path.dirname(__file__), "mock_data")


def _load(name: str):
    with open(os.path.join(DATA_DIR, f"{name}.json")) as f:
        return json.load(f)


# ---------- Tool schemas (force the model's output shape) ----------

NEGOTIATE_TOOL = {
    "name": "propose_itinerary_options",
    "description": "Return the negotiated itinerary options for the group.",
    "input_schema": {
        "type": "object",
        "properties": {
            "detected_priorities": {
                "type": "object",
                "description": "Map of participant name -> their detected priority in one short phrase",
            },
            "conflicts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "between": {"type": "array", "items": {"type": "string"}},
                        "description": {"type": "string"},
                    },
                    "required": ["between", "description"],
                },
            },
            "options": {
                "type": "array",
                "minItems": 3,
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "tag": {"type": "string"},
                        "title": {"type": "string"},
                        "hotel": {"type": "string"},
                        "food": {"type": "string"},
                        "activities": {"type": "string"},
                        "budget_pp": {"type": "integer"},
                        "matches": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["id", "tag", "title", "hotel", "food", "activities", "budget_pp", "matches"],
                },
            },
            "recommended_option_id": {"type": "string"},
            "ai_message": {"type": "string", "description": "A one-to-two sentence quote from Travex to show in the chat, e.g. 'I understand everyone's priorities...'"},
        },
        "required": ["detected_priorities", "conflicts", "options", "recommended_option_id", "ai_message"],
    },
}

REPLAN_TOOL = {
    "name": "propose_replan",
    "description": "Return alternatives after a travel disruption.",
    "input_schema": {
        "type": "object",
        "properties": {
            "alert_message": {"type": "string"},
            "ai_explanation": {"type": "string"},
            "alternatives": {
                "type": "array",
                "minItems": 2,
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "budget_delta_pct": {"type": "number"},
                        "reason": {"type": "string"},
                    },
                    "required": ["name", "budget_delta_pct", "reason"],
                },
            },
            "verification": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string"},
                        "passed": {"type": "boolean"},
                    },
                    "required": ["label", "passed"],
                },
            },
        },
        "required": ["alert_message", "ai_explanation", "alternatives", "verification"],
    },
}


def _force_tool_call(system: str, user_content: str, tool: dict) -> dict:
    resp = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        system=system,
        tools=[tool],
        tool_choice={"type": "tool", "name": tool["name"]},
        messages=[{"role": "user", "content": user_content}],
    )
    for block in resp.content:
        if block.type == "tool_use":
            return block.input
    raise RuntimeError("Model did not return a tool_use block")


# ---------- Public functions ----------

def negotiate(req: NegotiateRequest) -> NegotiateResponse:
    hotels = _load("hotels")
    dining = _load("dining")
    activities = _load("activities")

    transcript = "\n".join(f"{m.sender}: {m.text}" for m in req.messages)

    system = (
        "You are Travex, an autonomous AI travel-planning agent that joins a group's "
        "chat and negotiates a trip everyone can agree on. You are given: the group's "
        "chat transcript, and a fixed catalogue of real bookable hotels, dining "
        "options, and activities (with prices). "
        "Detect each participant's priority from what they said. Identify direct "
        "conflicts between participants (e.g. one wants luxury dining, another wants "
        "a tight budget). Propose exactly 3 distinct itinerary options that trade off "
        "differently: a comfort/luxury-leaning option, a balanced option, and a "
        "budget/experience-leaning option. Every hotel/food/activity name you use in "
        "an option MUST come from the provided catalogue — never invent a price or a "
        "name. budget_pp is the sum of hotel (x nights, assume 3 nights), food, and "
        "activities per person. Mark exactly one option as RECOMMENDED in its tag if "
        "it best balances the group's stated conflicts."
    )

    user_content = (
        f"TRIP: {req.trip_name}\n"
        f"PARTICIPANTS: {', '.join(req.participants)}\n"
        f"BUDGET CAP PER PERSON: {req.budget_pp or 'not specified'}\n\n"
        f"CHAT TRANSCRIPT:\n{transcript}\n\n"
        f"HOTEL CATALOGUE:\n{json.dumps(hotels, indent=2)}\n\n"
        f"DINING CATALOGUE:\n{json.dumps(dining, indent=2)}\n\n"
        f"ACTIVITY CATALOGUE:\n{json.dumps(activities, indent=2)}\n"
    )

    result = _force_tool_call(system, user_content, NEGOTIATE_TOOL)
    return NegotiateResponse(**result)


def replan(req: DisruptionRequest) -> ReplanResponse:
    hotels = [h for h in _load("hotels") if h["name"] != req.affected_item]

    system = (
        "You are Travex's monitoring agent. A booked item in the group's confirmed "
        "trip has just been disrupted. Your job: explain what happened in one plain "
        "sentence, then propose 2-3 real alternatives from the provided catalogue "
        "(excluding the disrupted item, which has already been removed from the "
        "catalogue you're given) that preserve the group's original budget and "
        "comfort level as closely as possible. budget_delta_pct is the percentage "
        "change vs. the original item's price (negative = cheaper, positive = more "
        "expensive). Also return a short verification checklist confirming what you "
        "checked before proposing these (price, availability, weather, group "
        "preference match) — mark each true only if it's something you actually "
        "reasoned about above."
    )

    user_content = (
        f"TRIP: {req.trip_name}\n"
        f"CURRENT OPTION ID: {req.current_option_id}\n"
        f"DISRUPTION TYPE: {req.disruption_type}\n"
        f"AFFECTED ITEM: {req.affected_item}\n\n"
        f"REMAINING HOTEL CATALOGUE:\n{json.dumps(hotels, indent=2)}\n"
    )

    result = _force_tool_call(system, user_content, REPLAN_TOOL)
    return ReplanResponse(**result)
