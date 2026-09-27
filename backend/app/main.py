from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .schemas import NegotiateRequest, NegotiateResponse, DisruptionRequest, ReplanResponse
from . import agent

app = FastAPI(title="Travex API")

# Wide open for hackathon speed. Tighten allow_origins before you share the
# deployed URL publicly if that matters to you.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/negotiate", response_model=NegotiateResponse)
def negotiate(req: NegotiateRequest):
    try:
        return agent.negotiate(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/replan", response_model=ReplanResponse)
def replan(req: DisruptionRequest):
    try:
        return agent.replan(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---- Demo helper: one-click disruption trigger for the stage demo ----
# Lets your Integration/Demo lead fire a disruption with a single button
# press instead of typing a full DisruptionRequest body live on stage.
@app.post("/simulate/hotel-cancelled", response_model=ReplanResponse)
def simulate_hotel_cancelled(trip_name: str, current_option_id: str, hotel_name: str):
    req = DisruptionRequest(
        trip_name=trip_name,
        current_option_id=current_option_id,
        disruption_type="hotel_cancelled",
        affected_item=hotel_name,
    )
    return agent.replan(req)
