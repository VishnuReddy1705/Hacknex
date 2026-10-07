# ChronosAI — Video Understanding & Temporal Reasoning

> **HNX26PSI02 — HackNex 2026 Problem Statement 02**  
> *"Not just what happened — what happened, when, in what order, and for how long."*

---

## 1. Project Overview & Innovation

Traditional computer vision applications are limited to frame-level object detection (e.g. "person detected", "truck detected"). **ChronosAI** introduces an **Object-Aware Temporal Event Graph** coupled with **Timestamp-Grounded Question Answering**.

Instead of piping raw video into an LLM and hoping for non-hallucinated timecodes, ChronosAI extracts persistent spatial trajectories, converts state transitions into semantic events, generates directed temporal relationships (`BEFORE`, `AFTER`, `IMMEDIATELY_BEFORE`, `DURING`, `OVERLAPS`, `COUNT`, `DURATION`), and resolves natural-language queries with exact timestamps and visual evidence.

---

## 2. Architecture

```
  USER / BROWSER
        │
        ▼
  React Web Dashboard (HTML5 Player + Interactive Scrubber)
        │ REST API
        ▼
  FastAPI Backend
        │
        ▼
  OpenCV Frame Extraction & Stride Sampling (Configurable PROCESS_FPS)
        │
        ▼
  Ultralytics YOLOv8 Detection (Person, Vehicles, Luggage, Equipment)
        │
        ▼
  ByteTrack Multi-Object Tracking (Persistent IDs: P01, truck_1)
        │
        ▼
  Event Detection State Machine (Zone entries, stationary, alarms)
        │
        ▼
  TEMPORAL REASONING ENGINE ──> Builds Object-Aware Temporal Event Graph
        │
        ▼
  Question Parser ──> Extracts { target_event, relation, target_object }
        │
        ▼
  Evidence Retrieval & Answer Formulation ──> Grounded MM:SS Timestamps
        │
        ▼
  Evidence-Based Answer + Clickable Video Seek Timestamps
```

---

## 3. Core Features

- **Frame-Exact Mathematical Timestamps:** Derived directly from camera FPS ($t = \frac{\text{frame}}{\text{FPS}}$), never hallucinated.
- **Identity Preservation:** ByteTrack maintains persistent tracks (`Worker P01`, `Truck #1`) through brief occlusions.
- **Object-Aware Temporal Event Graph:** Database-persisted directed edges encoding:
  - `BEFORE` / `AFTER`
  - `IMMEDIATELY_BEFORE` / `IMMEDIATELY_AFTER`
  - `DURING` / `OVERLAPS`
  - `STARTS_BEFORE` / `ENDS_AFTER`
  - `DURATION` / `TIME_DIFFERENCE`
- **Zero-API-Key Offline MVP:** 100% of temporal reasoning and question answering functions without an external LLM key.
- **Optional VLM/LLM Enhancement:** Integrates with Gemini / OpenAI via `.env` to optionally verify visual evidence.
- **Click-to-Seek Video Player:** Clicking any timestamp in the answer or evidence immediately seeks the HTML5 player to that moment.

---

## 4. Technology Stack

- **Frontend:** React 19, Vite, TypeScript, Tailwind CSS, Lucide Icons, HTML5 Video.
- **Backend:** Python 3.12, FastAPI, Uvicorn, Pydantic Settings.
- **Computer Vision:** OpenCV, Ultralytics YOLOv8, ByteTrack (Kalman Filter + Hungarian Matching).
- **Database:** SQLite (tables: `videos`, `objects`, `object_tracks`, `events`, `event_relationships`, `questions`, `answers`).

---

## 5. Quickstart & Installation (Windows 10/11)

### Step 1: Virtual Environment & Dependencies
```powershell
# From the repository root
python -m venv backend\.venv

# Activate virtual environment
.\backend\.venv\Scripts\Activate.ps1

# Install Python requirements
pip install -r backend\requirements.txt
```

### Step 2: Configure Environment (Optional LLM)
```powershell
# Copy the example environment file
cp backend\.env.example .env
```
*Note: The system works 100% out-of-the-box without an LLM API key!*

### Step 3: Run the Backend
```powershell
.\backend\.venv\Scripts\uvicorn.exe backend.app.main:app --host 127.0.0.1 --port 8000
```
Backend API runs at: `http://127.0.0.1:8000` (Swagger docs at `/docs`).

### Step 4: Run the Frontend
In a new terminal window:
```powershell
cd frontend
npm install
npm run dev
```
Frontend dashboard runs at: `http://127.0.0.1:5173`.

---

## 6. Official Section 18 Benchmark Verification

To seed the facility surveillance benchmark scenario and run the automated test suite:

```powershell
# 1. Seed benchmark scenario into SQLite & build Event Graph
python -m backend.app.utils.seed_timesense_demo

# 2. Run the test suite
python -m unittest discover -s tests
```

### Benchmark Scenario:
- `00:05` &rarr; Truck appears in driveway
- `00:12` &rarr; Delivery truck arrives at dock
- `00:20` &rarr; Worker P01 approaches truck
- `00:27` &rarr; Worker P01 enters restricted zone
- `00:35` &rarr; Worker P01 exits restricted zone
- `00:47` &rarr; Safety alarm activates
- `01:20` &rarr; Machine starts operation
- `02:10` &rarr; Machine stops
- `02:35` &rarr; Machine starts operation
- `03:10` &rarr; Machine stops

### Benchmark Query Results:
| Query | System Answer | Grounded Timestamps |
| :--- | :--- | :--- |
| *"Who entered the restricted area after the truck arrived?"* | Worker P01 entered restricted zone at 00:27, 15s after Delivery truck arrived at dock at 00:12. | `00:12`, `00:27` |
| *"How many times did the machine stop?"* | The machine stopped 2 times, at 02:10, 03:10. | `02:10`, `03:10` |
| *"What happened immediately before the alarm?"* | Immediately before Safety alarm activated at 00:47, Worker P01 exited restricted zone occurred at 00:35 (12.0s prior). | `00:35`, `00:47` |
| *"What happened first?"* | The first recorded event was Truck appeared in driveway at 00:05. | `00:05` |

---

## 7. REST API Endpoints

- `POST /api/videos/upload` — Upload raw MP4/AVI/MOV video and extract OpenCV metadata.
- `POST /api/videos/{video_id}/process` — Trigger background detection, tracking, event extraction, and graph construction.
- `GET /api/videos/{video_id}/status` — Real-time frame-by-frame processing progress.
- `GET /api/videos/{video_id}/timeline` — Retrieve the Object-Aware Temporal Event Graph with all directed relationship edges.
- `GET /api/videos/{video_id}/objects` — List persistent tracked entities (`P01`, `truck_1`) with time intervals.
- `GET /api/videos/{video_id}/events` — Chronological list of semantic events.
- `POST /api/videos/{video_id}/ask` — Submit natural-language temporal question, returning timestamp-grounded answer with evidence.
- `GET /api/videos/{video_id}/stream` — Stream video with HTTP 206 byte-range seeking support.
- `GET /api/health` — Service health check and GPU acceleration status.

---

## 8. Docker Deployment

```bash
docker-compose up --build
```
- Backend exposed on port `8000`.
- Frontend exposed on port `5173`.
