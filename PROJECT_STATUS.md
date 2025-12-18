# Project Status: Martinique Weather Dashboard

**Last Updated:** 2025-12-17 17:15 PST
**Upwork Job:** Météo France API weather data extraction and visualization for Martinique
**Client:** Remi (amateur weather enthusiast, passionate about Martinique)
**Status:** DEPLOYED - SMS Alert System Live on Render, Awaiting Feedback
**Price:** $50 agreed (+ excellent review + future work commitment)
**Version:** 1.2

---

## Quick Context for New Sessions

Weather data extraction and visualization system for Martinique using Météo France API. Now includes full SMS alert subscription system with Twilio integration.

### Latest Update (2025-12-17 17:15)

**DEPLOYED TO RENDER**

Live URL: **https://meteo-martinique.onrender.com**

GitHub Repo: **https://github.com/mastervb99/meteo-martinique**

Deployment completed:
- Initialized git repository
- Created GitHub repo (mastervb99/meteo-martinique)
- Deployed to Render.com (free tier)
- Fixed Dockerfile to run API server instead of scheduler
- SMS alerts subscription page is live and functional

**Current Status:**
- SMS Alert subscription page: LIVE
- Weather dashboard pages: NOT YET BUILT (Phase 2)
- Nav links (Aujourd'hui, Prévisions, Cartes): Placeholder only

**Message sent to Remi:**
> J'ai mis en ligne une première version: https://meteo-martinique.onrender.com
> C'est le système d'abonnement aux alertes SMS. Le tableau de bord météo complet est la prochaine étape.

**Awaiting:** Remi's feedback before proceeding to Phase 2 (full weather dashboard).

---

## New Files Added (2025-12-17)

| File | Purpose |
|------|---------|
| `sms_service.py` | Twilio SMS client, OTP service, AlertService with profile-based templates |
| `subscriptions.py` | SQLite subscription management (CRUD, history, stats) |
| `api.py` | FastAPI REST endpoints for frontend |
| `alert_broadcaster.py` | Broadcasts alerts to subscribers when vigilance changes |
| `static/alerte.html` | API-connected version of Remi's mockup |

---

## SMS Alert System Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│  alerte.html    │────▶│  FastAPI     │────▶│  Twilio SMS     │
│  (Frontend)     │     │  (api.py)    │     │  (sms_service)  │
└─────────────────┘     └──────────────┘     └─────────────────┘
                              │
                              ▼
                        ┌──────────────┐
                        │   SQLite     │
                        │ (subscriptions)│
                        └──────────────┘

┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Vigilance      │────▶│  Scheduler   │────▶│  Broadcaster    │──▶ SMS to all
│  Data Update    │     │              │     │                 │    subscribers
└─────────────────┘     └──────────────┘     └─────────────────┘
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serves alerte.html subscription page |
| `/api/health` | GET | Health check + SMS config status |
| `/api/otp/send` | POST | Send OTP verification code |
| `/api/otp/verify` | POST | Verify OTP code |
| `/api/subscribe/confirm` | POST | Confirm subscription, send welcome SMS |
| `/api/subscribe/test` | POST | Send test alert to subscriber |
| `/api/subscribe/{ref}` | GET | Get subscription details |
| `/api/subscribe/update` | PUT | Update profile |
| `/api/subscribe/unsubscribe` | DELETE | Unsubscribe |
| `/api/webhook/incoming` | POST | Twilio webhook for STOP commands |
| `/api/stats` | GET | Subscription statistics |
| `/api/profiles` | GET | Available profile types |

### Subscriber Profiles

1. **Particulier** - General public, standard advice
2. **Professionnel (BTP / agriculture)** - Construction/farming workers
3. **Nautique / pêche / plaisance** - Sailors, fishers, boaters
4. **Tourisme / plages** - Tourists, beach activities

Each profile receives customized safety advice per phenomenon type.

### Alert Flow

1. Scheduler runs vigilance check every 30 minutes
2. If vigilance level increases to Yellow (2) or higher → triggers broadcaster
3. Broadcaster sends SMS to all active verified subscribers
4. Each subscriber gets profile-specific advice
5. Alert history logged to database

---

## CLI Commands (Updated)

```bash
python main.py --help           # Show all commands
python main.py demo             # Run demo with sample data
python main.py extract          # Extract live data (needs API key)
python main.py schedule         # Start automated scheduler (includes SMS broadcast)
python main.py api              # Start SMS alerts API server (port 8000)
python main.py api -p 3000      # Custom port
python main.py info             # Show configuration status (incl. Twilio)
```

---

## Configuration Required

### .env file

```bash
# Météo France API
METEO_FRANCE_APP_ID=your_app_id
METEO_FRANCE_API_KEY=your_api_key

# Twilio SMS (for alerts)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```

---

## Dependencies (Updated)

| Package | Version | Purpose |
|---------|---------|---------|
| meteofrance-api | 1.4.0 | Météo France API client |
| folium | 0.20.0 | Interactive maps |
| plotly | 6.5.0 | Charts |
| pandas | 2.3.3 | Data processing |
| schedule | 1.2.2 | Task scheduling |
| typer | 0.20.0 | CLI framework |
| rich | 14.2.0 | Console output |
| python-dotenv | 1.2.1 | Environment variables |
| **twilio** | **9.3.0** | **SMS service** |
| **fastapi** | **0.115.0** | **REST API** |
| **uvicorn** | **0.32.0** | **ASGI server** |
| **pydantic** | **2.10.0** | **Data validation** |
| pytest | 9.0.2 | Testing |

---

## File Structure (Updated)

```
martinique_weather/
├── main.py                # Typer CLI (demo/extract/schedule/api/info)
├── config.py              # Configuration + Twilio credentials
├── utils.py               # Logging setup
├── weather_extractor.py   # Météo France API extraction
├── map_generator.py       # Folium maps
├── chart_generator.py     # Plotly charts
├── scheduler.py           # Automated scheduler (now with SMS broadcast)
├── sms_service.py         # NEW: Twilio SMS + OTP + AlertService
├── subscriptions.py       # NEW: SQLite subscription management
├── api.py                 # NEW: FastAPI REST endpoints
├── alert_broadcaster.py   # NEW: Broadcasts to all subscribers
├── static/
│   └── alerte.html        # NEW: API-connected subscription page
├── requirements.txt       # Updated with twilio, fastapi, uvicorn, pydantic
├── .env.example           # Updated with Twilio config
├── README.md              # User documentation
├── PROJECT_STATUS.md      # This file
├── venv/                  # Virtual environment
├── tests/                 # Unit tests
├── logs/                  # Execution logs
└── output/
    ├── data/
    │   ├── subscriptions.db      # NEW: SQLite database
    │   ├── last_alert_state.json # NEW: Alert state tracking
    │   └── ...
    ├── maps/
    └── charts/
```

---

## Completed Work

| Component | Status | Notes |
|-----------|--------|-------|
| config.py | Done | Martinique coords, vigilance colors, Twilio config |
| utils.py | Done | Logging setup |
| weather_extractor.py | Done | Forecasts, hourly, vigilance, rain |
| map_generator.py | Done | Vigilance, forecast, rain maps |
| chart_generator.py | Done | Temperature, hourly dashboard, gauge |
| scheduler.py | Done | Now includes SMS broadcast on vigilance update |
| main.py | Done | Added `api` command |
| **sms_service.py** | **Done** | **Twilio SMS, OTP, profile-based alerts** |
| **subscriptions.py** | **Done** | **SQLite CRUD, history, stats** |
| **api.py** | **Done** | **FastAPI endpoints** |
| **alert_broadcaster.py** | **Done** | **Vigilance-triggered broadcasting** |
| **static/alerte.html** | **Done** | **Frontend connected to API** |

---

## Next Steps

1. **Awaiting Remi's Feedback** - On deployed SMS alerts page
2. **Phase 2: Weather Dashboard** - Build full dashboard pages (see plan below)
3. **Twilio Setup** - Remi needs to create Twilio account and provide credentials
4. **Final Deployment** - Move to o2switch if needed for production

---

## Phase 2 Plan: Full Weather Dashboard (PENDING APPROVAL)

### Overview

Build complete weather dashboard with 4 main pages accessible via navigation:

| Page | Route | Description |
|------|-------|-------------|
| Aujourd'hui | `/` or `/today` | Current conditions + 24h forecast |
| Prévisions | `/forecast` | 7-day forecast for all cities |
| Cartes | `/maps` | Interactive vigilance & weather maps |
| Alertes | `/alerts` | SMS subscription (already done) |

### Phase 2.1: Backend API Endpoints

New endpoints to add to `api.py`:

```
GET /api/weather/current          # Current conditions for Fort-de-France
GET /api/weather/hourly           # 48-hour hourly forecast
GET /api/weather/forecast         # 7-day forecast all cities
GET /api/weather/vigilance        # Current vigilance alerts
GET /api/weather/rain             # Rain radar data
GET /api/maps/vigilance           # Embedded vigilance map HTML
GET /api/maps/forecast            # Embedded forecast map HTML
GET /api/charts/temperature       # Temperature trend chart
GET /api/charts/hourly            # Hourly dashboard chart
```

### Phase 2.2: Frontend Pages

**Option A: Jinja2 Templates (Server-rendered)**
- Simple, fast to implement
- Single codebase
- Good for SEO

**Option B: Static HTML + JavaScript (Like alerte.html)**
- Consistent with existing page style
- API-driven, modern feel
- More interactive

**Recommendation:** Option B (matches Remi's design style)

### Phase 2.3: Page Designs

#### Page 1: Aujourd'hui (Today)
```
┌─────────────────────────────────────────────────────────┐
│ Header (same as alerte.html)                            │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────────────────────┐ │
│ │ Current Weather │ │ Vigilance Status                │ │
│ │ Fort-de-France  │ │ Wind: 🟢  Rain: 🟡  Waves: 🟢  │ │
│ │ 28°C Ensoleillé │ │                                 │ │
│ │ Humidity: 78%   │ │                                 │ │
│ │ Wind: 25 km/h   │ │                                 │ │
│ └─────────────────┘ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 24-Hour Forecast Chart (Plotly embedded)            │ │
│ └─────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Hourly Breakdown (scrollable cards)                 │ │
│ │ 14:00  15:00  16:00  17:00  18:00  19:00 ...       │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

#### Page 2: Prévisions (7-Day Forecast)
```
┌─────────────────────────────────────────────────────────┐
│ Header                                                  │
├─────────────────────────────────────────────────────────┤
│ City Selector: [Fort-de-France ▼]                       │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 7-Day Cards                                         │ │
│ │ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐   │ │
│ │ │ Lun │ │ Mar │ │ Mer │ │ Jeu │ │ Ven │ │ Sam │   │ │
│ │ │ ☀️  │ │ ⛅  │ │ 🌧️  │ │ ☀️  │ │ ☀️  │ │ ⛈️  │   │ │
│ │ │28/24│ │27/23│ │26/23│ │29/24│ │30/25│ │27/23│   │ │
│ │ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘   │ │
│ └─────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Temperature Trend Chart (7 days)                    │ │
│ └─────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ All Cities Table                                    │ │
│ │ City          | Today | Tomorrow | Precipitation   │ │
│ │ Fort-de-France| 28°C  | 27°C     | 20%            │ │
│ │ Le Lamentin   | 29°C  | 28°C     | 15%            │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

#### Page 3: Cartes (Maps)
```
┌─────────────────────────────────────────────────────────┐
│ Header                                                  │
├─────────────────────────────────────────────────────────┤
│ Map Type: [Vigilance ▼] [Températures] [Précipitations] │
│ ┌─────────────────────────────────────────────────────┐ │
│ │                                                     │ │
│ │              Folium Map (iframe)                    │ │
│ │              Full Martinique view                   │ │
│ │              Interactive markers                    │ │
│ │                                                     │ │
│ └─────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Legend + Map Controls                               │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Phase 2.4: Implementation Steps

1. **Create page templates** (static/today.html, forecast.html, maps.html)
2. **Add API routes** for weather data endpoints
3. **Integrate existing generators** (map_generator, chart_generator) with API
4. **Connect frontend** to API with JavaScript fetch calls
5. **Update navigation** links in all pages
6. **Add data caching** to reduce API calls
7. **Test all pages** with demo and live data
8. **Deploy update** to Render

### Phase 2.5: Data Flow

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ Météo France API │────▶│ weather_extractor│────▶│ JSON/CSV Cache   │
└──────────────────┘     └──────────────────┘     └──────────────────┘
                                                          │
                                                          ▼
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ Frontend Pages   │◀────│ FastAPI Routes   │◀────│ Generators       │
│ (HTML + JS)      │     │ /api/weather/*   │     │ (maps, charts)   │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

### Phase 2.6: Estimated New Files

| File | Purpose |
|------|---------|
| `static/index.html` | Today page (redirect or main) |
| `static/today.html` | Current conditions page |
| `static/forecast.html` | 7-day forecast page |
| `static/maps.html` | Interactive maps page |
| `static/css/style.css` | Shared styles (extracted from alerte.html) |
| `static/js/api.js` | Shared API client functions |

### Phase 2.7: Dependencies

No new dependencies required - uses existing:
- FastAPI (routing)
- Folium (maps)
- Plotly (charts)
- Pandas (data processing)

### Timeline Estimate

- Phase 2.1 (API): 2-3 hours
- Phase 2.2-2.3 (Frontend): 4-6 hours
- Phase 2.4-2.5 (Integration): 2-3 hours
- Phase 2.6 (Testing/Deploy): 1-2 hours

**Total: ~10-15 hours**

### Awaiting

- Remi's approval to proceed
- Any design preferences or changes
- Priority order of pages

---

## Testing the SMS System

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure Twilio (in .env)
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=...

# 3. Start API server
python main.py api

# 4. Open browser
# http://localhost:8000 → Subscription page
# http://localhost:8000/docs → API documentation (Swagger)

# 5. Test subscription flow
# - Enter phone number
# - Click "Envoyer le code"
# - Enter OTP from SMS
# - Click "Valider le code"
# - Check consent box
# - Click "Confirmer l'abonnement"
# - Click "Tester une alerte" to receive test SMS
```

---

## Client Communication History

### 2025-12-16
- Sent demo visualization as proof of concept
- Negotiated $50 price
- Client wants live server demo

### 2025-12-17 (AM)
- Client will provide design example later
- Hosting: o2switch with CRON
- Requested demo on Render.com
- Template file issue (merci.html not accessible)

### 2025-12-17 (PM)
- Client sent `alerte.rar` with SMS alert mockup
- Full backend integration completed
- Sent message asking for proposal acceptance and customization preferences

### 2025-12-17 (Evening)
- Client sent contract and asked to deploy online
- Created GitHub repo: mastervb99/meteo-martinique
- Deployed to Render: https://meteo-martinique.onrender.com
- Fixed Dockerfile (was running scheduler instead of API)
- SMS alerts page now live
- Sent deployment link to Remi (EN/FR)
- Created Phase 2 plan for full weather dashboard
- Awaiting Remi's feedback before proceeding

---

**Author**: Vafa Bayat
**Contact**: vafa@bitscopic.com
