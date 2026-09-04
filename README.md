# WiSense - Wi-Fi Human Movement Sensing Platform

Detect human movement using Wi-Fi Channel State Information (CSI).

## Quick Start (Windows)

Option A - Docker:
  copy .env.example .env
  docker compose up --build
  Open http://localhost:5173

Option B - Manual:
  Backend:
    cd backend
    python -m venv venv
    venv\Scripts\Activate
    pip install -r requirements.txt
    uvicorn app.main:app --reload

  Frontend:
    cd frontend
    npm install
    npm run dev

  Open http://localhost:5173

## First Run
1. Register and login
2. Default model auto-generated on first startup
3. Dashboard - Start Simulator
4. Switch between NO_MOVEMENT, MOVEMENT, WALKING

## Limitation
A web browser cannot access raw Wi-Fi CSI. Simulation mode uses synthetic signals.
Real sensing requires compatible hardware (ESP32).
