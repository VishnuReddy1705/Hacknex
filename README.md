# TemporalLens — Video Understanding & Temporal Reasoning Engine

> **HackNex 2026 Problem Statement 02 (PS02)**  
> Autonomous Computer Vision & Temporal Grounding System that answers *What happened*, *When it happened*, and *In what order* with frame-exact visual evidence.

---

## 1. Architectural Concept

```
  VIDEO FILE
      │
      ▼
┌───────────────────────────────┐
│     Video Ingestion (OpenCV)  │ ──> Computes FPS, resolution & frame-exact timestamps
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│     Object Detection (YOLO)   │ ──> Pretrained spatial bounding boxes & surveillance classes
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│   Object Tracking (ByteTrack) │ ──> Persistent track IDs (Person #1, Backpack #2)
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│  Temporal Event Engine (CV)   │ ──> Zone crossings, stationary displacement, unattended baggage
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│   SQLite Temporal Memory      │ ──> Indexed chronological timeline with start/end timecodes
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│ Deterministic Query Reasoner  │ ──> Evaluates BEFORE, AFTER, BETWEEN, DURATION, COUNT, SEQUENCE
└──────────────┬────────────────┘
               │
               ▼
    ANSWER + TIMECODE + CLICKABLE VISUAL EVIDENCE
```

---

## 2. Six-Pillar Philosophy

1. **SEE (Detection):** Ultralytics YOLOv8 extracts target entities (`person`, `backpack`, `handbag`, `suitcase`, `truck`, `car`).
2. **TRACK (Identity):** ByteTrack (Kalman Filter + Hungarian matching) maintains consistent track IDs across frames and occlusion.
3. **UNDERSTAND (Event Extraction):** Geometric state machines analyze spatial trajectories, velocity, displacement thresholds, and interaction proximity.
4. **REMEMBER (Temporal Memory):** Structured SQLite relational database records start/end timecodes, frame intervals, and entity relationships.
5. **REASON (Temporal Engine):** Resolves temporal constraints (`BEFORE`, `AFTER`, `BETWEEN`, `HOW LONG`, `HOW MANY`) deterministically.
6. **PROVE (Evidence Grounding):** Every answer is accompanied by exact timestamps and clickable seek targets that jump directly to that moment in the video.

---

## 3. Supported Temporal Events & Logic

| Event Type | State Transition & Logic Trigger |
| :--- | :--- |
| `PERSON_ENTERED` | Target person track initial observation frame / zone crossing |
| `PERSON_EXITED` | Target person track cessation / departure from camera FOV |
| `OBJECT_APPEARED` | New inanimate object detection (backpack, luggage, cargo) |
| `OBJECT_STATIONARY` | Object displacement $\le$ 30px maintained over configurable time threshold |
| `OBJECT_LEFT_UNATTENDED` | Associated carrier moves $>180\text{px}$ away while object remains stationary for $>4\text{s}$ |
| `OBJECT_PICKED_UP` | Secondary entity intersects unattended object coordinates and clears item |
| `LOITERING` | Person remains within bounded spatial radius for $>8\text{s}$ |

---

## 4. Key Questions Supported by the Reasoning Engine

- **Order / Sequence:** *"What happened first?"*, *"What was the last event?"*, *"Show the full sequence."*
- **Relative Temporal Relations:** *"Who entered after Person 1?"*, *"What happened before the last exit?"*
- **Intervals & Intermediates:** *"What happened between Person 1 entering and leaving?"*
- **Duration Calculations:** *"How long was the backpack unattended?"*, *"How long did Person 1 stay?"*
- **Entity Inquiries & Counts:** *"How many people were tracked?"*, *"When did the bag appear?"*

---

## 5. Quickstart & Reproduction Guide

### Prerequisites
- Python 3.10 – 3.12
- Node.js v18+ and npm
- GPU (NVIDIA RTX with CUDA) or multi-core CPU

### Step 1: Backend Setup
```bash
# From repository root
python -m venv backend/.venv

# Activate virtual environment (Windows PowerShell)
.\backend\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r backend/requirements.txt

# Run the FastAPI server
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```
Backend runs at: `http://127.0.0.1:8000` (API documentation at `/docs`).

### Step 2: Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend runs at: `http://127.0.0.1:5173`.

### Step 3: Run Seed Benchmark Scenario (Optional)
To immediately test the benchmark scenario with seeded ground truth:
```bash
python -m backend.app.utils.seed_benchmark_scenario
python -m backend.app.utils.test_reasoner
```

---

## 6. Monorepo Project Structure

```
Hacknex/
├── backend/
│   ├── app/
│   │   ├── api/                 # FastAPI routes (videos, events, entities, query)
│   │   ├── database/            # SQLite session and SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/
│   │   │   ├── video_processor.py   # YOLOv8 + ByteTrack pipeline
│   │   │   ├── event_engine.py      # Spatial & temporal event extractor
│   │   │   └── temporal_reasoner.py # Deterministic query engine
│   │   ├── utils/               # Synthetic video generator & benchmark test
│   │   └── main.py              # Application entrypoint
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # VideoPlayer, TopBar, Sidebar, EvidenceCard, EmptyUpload
│   │   ├── pages/               # Overview, VideoAnalysis, EventTimeline, AskVideo, Entities, Settings
│   │   ├── services/            # Typed API client
│   │   ├── types/               # TypeScript data models
│   │   └── App.tsx              # Application shell & state manager
│   ├── package.json
│   └── vite.config.ts
├── data/
│   ├── uploads/                 # Uploaded raw videos
│   ├── processed/               # Annotated video tracks
│   └── database/                # SQLite database file
└── README.md
```

---

## 7. Submission Checklist for HackNex 2026 PS02

- [x] **Working System:** End-to-end full-stack app with video upload, background processing, and playback.
- [x] **Data Pipeline:** Video $\rightarrow$ OpenCV metadata $\rightarrow$ YOLO detection $\rightarrow$ ByteTrack persistent IDs.
- [x] **Core Reasoning:** Deterministic temporal engine answering BEFORE, AFTER, BETWEEN, HOW LONG, COUNT, ORDER.
- [x] **Evidence-Grounded:** Exact start/end timestamps and clickable jump-to-timecode video seeking.
- [x] **Sample I/O & Verification:** Automated test suite verifying question answering with timestamps.
