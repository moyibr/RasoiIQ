# 🌱 Anna Setu — SIH 2026 Prototype

**Problem Statement:** SIH26234 — AI-powered food waste reduction and redistribution platform for institutional kitchens and food processing units.

**Core flow:** Kitchen data → Demand forecast → Production plan → Surplus detection → Rescue-window urgency → NGO matching → Route to NGO → Unified dashboard

---

## Project Structure

```
food-waste-platform/
├── backend/          # Python · FastAPI · SQLAlchemy · PostgreSQL (Supabase)
├── frontend/         # Next.js 14 · TypeScript · Tailwind CSS · Recharts · MapLibre GL
└── README.md
```

---

## Prerequisites

| Tool | Version |
|---|---|
| Python | 3.11+ |
| Node.js | 18+ |
| npm / yarn | latest |
| PostgreSQL | via Supabase (cloud) |

---

## 1. Backend Setup

### 1.1 Install dependencies

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 1.2 Configure environment

```bash
cp .env.example .env
```

Edit `.env` and configure the following variables (all optional):

* `DATABASE_URL`: Set to a PostgreSQL connection string if you want to use PostgreSQL. Defaults to `sqlite:///./test.db` if unset.
* `GROQ_API_KEY`: Set this to a valid Groq API key (free at console.groq.com) to enable the hosted LLM fallback tier for sustainability reports. If Ollama is down, it will use Groq. If both are down, it falls back to a template.

```
DATABASE_URL=postgresql://postgres:<your-password>@<your-project>.supabase.co:5432/postgres
GROQ_API_KEY=your_groq_api_key_here
```

> **Where to find this:** Supabase Dashboard → Project Settings → Database → Connection string → URI mode. Use the "Direct connection" URI (port 5432), not the pooler.

### 1.3 Seed the database

This creates all tables and inserts 6 months of synthetic data:

```bash
cd backend
python -m scripts.seed_data
```

Expected output:
```
✓ Tables created
✓ Seeded: 1 kitchen, 8 food categories, 5 NGOs
✓ Generated: ~4,400 consumption records (6 months × 8 categories × 3 meals)
✓ Generated: ~4,400 production records
✓ Generated: ~1,200 surplus events
✓ Generated: ~183 sustainability metric rows
Seeding complete.
```

The script is **idempotent** — safe to re-run without duplicating data.

### 1.4 Run the backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

API docs available at: [http://localhost:8000/docs](http://localhost:8000/docs)

Health check: [http://localhost:8000/health](http://localhost:8000/health)

---

## 2. Frontend Setup

### 2.1 Install dependencies

```bash
cd frontend
npm install
```

### 2.2 Run the frontend

```bash
npm run dev
```

App available at: [http://localhost:3000](http://localhost:3000)

> Make sure the backend is running on port 8000 before opening the frontend, or you'll see API errors.

---

## 3. Regenerating Synthetic Data

To wipe and re-seed all synthetic data from scratch:

```bash
# From the backend/ directory with venv active
python -m scripts.seed_data
```

The script deletes existing rows before re-inserting, so the data is always fresh and consistent.

To export data as CSV instead of seeding into the DB, run:
```bash
python -m scripts.seed_data --export-csv
```
This writes CSV files to `backend/data/` (one per table).

---

## 4. API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `GET /health` | GET | Health check |
| `GET /anumaan/forecast` | GET | Automated demand forecast using Anumaan |
| `GET /surplus` | GET | Active surplus events with urgency |
| `POST /match` | POST | Ranked NGO list for a surplus event |
| `GET /route` | GET | Delivery route waypoints |
| `GET /dashboard/summary` | GET | Aggregated stats for dashboard |

Full interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 5. What's Real vs. Stubbed

This is a prototype. We are currently integrating Phase 2 (Anumaan XGBoost Model).

| Module | Status | Notes |
|---|---|---|
| **Database schema** | ✅ Real | All 8 tables created and normalized, including `consumption_history` |
| **Synthetic data generator** | ✅ Real | Data generation logic is live |
| **NGO seed profiles** | ✅ Real | 5 NGOs with real Bengaluru coordinates |
| **Dashboard UI** | ✅ Real | Wired to live API |
| **Surplus list UI** | ✅ Real | Wired to live API |
| **NGO match list UI** | ✅ Real | Wired to live API |
| **Map with NGO markers** | ✅ Real | Real MapLibre GL JS with OSM tiles |
| **Route polyline on map** | ✅ Real | Renders stub route data correctly |
| **Forecast chart** | ✅ Real | Recharts chart, renders Anumaan predictions |
| **`/anumaan/forecast` logic** | ✅ Real | Uses trained XGBoost model with auto-assembled lag and contextual features. |
| **`/surplus` logic** | 🟡 Stub | Returns hardcoded surplus events; Phase 2 will query live DB with rule-based detection |
| **`/match` logic** | 🟡 Stub | Returns hardcoded ranked NGOs; Phase 2 will use scoring engine (distance + capacity + preference) |
| **`/route` logic** | 🟡 Stub | Returns interpolated straight-line route; Phase 2 will use nearest-neighbor ordering |
| **`/dashboard/summary` logic** | 🟡 Stub | Returns hardcoded stats; Phase 2 will aggregate from DB |

### Phase 2a - Anumaan Integration Notes

**Kitchen-To-Location Mapping**
Since the Anumaan model was trained on specific Location IDs (Loc_1 to Loc_26), the demo kitchens are strictly mapped as follows:
- `K1_MainCampus` -> `Loc_3`
- `K2_HostelBlockA` -> `Loc_7`
- `K3_HostelBlockB` -> `Loc_15`

**Climatology Fallback for Contextual Features**
In a real deployment, advance contextual features like temperature, reservations, and online ratings are not perfectly known. We use a **climatology fallback** pattern for cold-start forecasting:
- `temp_celsius` and `rain_mm` use the historical seasonal average for that location/month.
- `reservations`, `cpi_index`, `online_rating`, and `competitor_promo` use the recent 30-day historical average.

**Historical Data Gap & Synthetic Bridge**
The raw `restaurant_demand_28k.csv` dataset ends in December 2025. Because demos will run in September 2026 (or later), there is a temporal gap. To ensure the automated lag features (`demand_yesterday`, `demand_7_days_ago`, `demand_ma7`) still work, we generate a **synthetic continuous bridge**. The `seed_anumaan.py` script automatically shifts 2025 data forward by 364 days to populate 2026 dates, ensuring seamless lag feature continuity right up to the demo date. Note that this bridge simply copies the exact, raw (noisy) historical values from 52 weeks prior rather than smoothing them or regenerating them via a fresh negative-binomial process.

### Not built (out of scope for now — P2)
- VRPTW routing solver (OR-Tools)
- Computer vision freshness detection
- Multi-role authentication
- SMS / push notifications
- LLM-generated sustainability reports (P1, not yet)

---

## 6. Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI 0.111 |
| ORM | SQLAlchemy 2.0 |
| Database | PostgreSQL via Supabase |
| Data validation | Pydantic v2 |
| Frontend framework | Next.js 14 (App Router) |
| Styling | Tailwind CSS 3 |
| Charts | Recharts 2 |
| Map | MapLibre GL JS 4 |
| Map tiles | OpenStreetMap (no API key required) |

---
*Built for Smart India Hackathon 2026 · Problem Statement SIH26234*

---

## Acknowledgements

RasoiIQ is built on top of the open-source project 'AI-Powered-Food-Reduction-and-Surplus-Distribution-Management' by Garv1105 (https://github.com/Garv1105/AI-Powered-Food-Reduction-and-Surplus-Distribution-Management), used under its license. Original LICENSE retained.

**Additions made in RasoiIQ:**
- **Food Quality Check (computer vision):** Added a `/quality/analyze` endpoint using OpenCV to assess food freshness via color variance, and a React frontend for image upload and score visualization.
- **ESG and Sustainability Analytics:** Added a `/reports/esg-analytics` backend endpoint to compute saved food, donated meals, and CO2e avoided, alongside a frontend dashboard with Recharts visualizations and a PDF download feature.
- **Processing Unit Monitor (simulated IoT):** Added the `IoTSensorData` database model, ingestion/simulation endpoints (`/iot/ingest`, `/iot/simulate`), rule-based alerting for temperature and downtime, and a live telemetry dashboard in the frontend.
- **Dependency Stabilization:** Removed strict pins in `requirements.txt` to allow building on modern Python (3.13) without native C++ compilation errors on Windows.
