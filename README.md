# Travex — Starter Kit

This is the real core of the project: the negotiation agent, the disruption/replan
agent, and the live group chat. Everything else from the deck (memories screen,
photo collage, video) is UI you build on top of this once the core loop works.

## What's real vs. what's still yours to build

| Piece | Status here |
|---|---|
| Group chat (multi-device, live) | **Real** — Firebase Firestore, wired |
| Preference detection + negotiation | **Real** — Claude API, structured JSON |
| Conflict detection | **Real** — part of the same negotiation call |
| 3-option itinerary generation | **Real** — grounded in mock_data catalogues |
| Disruption → replan | **Real logic**, manually-triggered demo endpoint |
| Verification checklist | **Real** — model reasons about it and returns it; wire real weather/price APIs later if you have time (see "Going further" below) |
| Photo collage / video / memories screen | **Not built here** — see day 6+ in your plan |

## 1. Backend setup (do this first)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then paste your real ANTHROPIC_API_KEY in
uvicorn app.main:app --reload --port 8000
```

Test it's alive: open `http://localhost:8000/health` — should return `{"status":"ok"}`.

Test the negotiation endpoint (this is your core agent — get this right before
touching any frontend code):

```bash
curl -X POST http://localhost:8000/negotiate \
  -H "Content-Type: application/json" \
  -d '{
    "trip_name": "Trip to Goa",
    "participants": ["Shreya", "Rayan", "Mohammed Zayan", "Mohammed Huzaif"],
    "messages": [
      {"sender": "Shreya", "text": "Food is non-negotiable. Michelin stars only!"},
      {"sender": "Rayan", "text": "Need a comfortable hotel. No hostels!"},
      {"sender": "Mohammed Zayan", "text": "Keep it within budget. More activities."},
      {"sender": "Mohammed Huzaif", "text": "I do not want to sit in cafes all day!"}
    ],
    "budget_pp": 2500
  }'
```

You should get back JSON with `detected_priorities`, `conflicts`, 3 `options`, and
`ai_message` — that's your entire negotiation engine working.

Test the disruption demo trigger (this is your "hotel cancellation" stage moment):

```bash
curl -X POST "http://localhost:8000/simulate/hotel-cancelled?trip_name=Trip%20to%20Goa&current_option_id=option_2&hotel_name=Hotel%20Arts"
```

## 2. Frontend setup

```bash
npx create-next-app@latest travex-frontend --tailwind --app
cd travex-frontend
npm install firebase
```

Then copy `frontend/lib`, `frontend/hooks`, `frontend/components` from this
starter into your new project, and copy `.env.local.example` → `.env.local`
with your real Firebase + backend values.

**Get Firebase values**: [console.firebase.google.com](https://console.firebase.google.com)
→ Create project → Build → Firestore Database → Create database (test mode is
fine for a hackathon) → Project settings → Add app (Web) → copy the config
values into `.env.local`.

Use `frontend/components/TripPage.example.jsx` as your starting page — copy it
to `app/trip/[tripId]/page.jsx` and adjust.

## 3. Demo day flow (maps directly to this code)

1. Open the trip page on 2-4 devices, each with a different `currentUser` — this is
   your live "group chat" moment from slide 2.
2. Everyone sends their preference message. Press **"Ask Travex to negotiate"**
   → calls `POST /negotiate` → renders the 3 cards from slide 3.
3. To trigger the "hotel cancelled" moment from slide 4: call
   `POST /simulate/hotel-cancelled` from a small "Simulate Disruption" button you
   add to the demo build (not shown to end users, just for your stage device) →
   render the alternatives + verification checklist.

## Going further (if you have spare time on days 5-6)

- **Real weather check**: sign up free at openweathermap.org, add a call in
  `agent.py`'s `replan()` before the LLM call, and pass the real forecast into
  the prompt so "Weather Forecast Checked" is grounded in a real API response.
- **Real price/availability shape**: Amadeus for Developers has a free
  self-service tier with sandbox flight/hotel search — same idea, wire it in
  and pass real (sandbox) results into the prompt.
- **Persistence**: swap the in-memory approach for writing negotiated results
  back into Firestore under `trips/{tripId}/plan` so a judge can refresh the
  page and still see the result.

## Team split suggestion for this codebase

- **Agent/Backend lead** → owns `backend/app/agent.py`, prompt tuning, mock data
- **Frontend lead** → owns `frontend/components/`, matching the deck's visuals
- **Data/Disruption engineer** → owns `mock_data/*.json`, the disruption demo
  button, and (if time) the real weather/price API wiring
- **Integration/Demo lead** → owns `.env` files, deployment, the `TripPage`
  wiring, and rehearsing the exact demo click-path
