# Project Status: Martinique Weather Dashboard

**Last Updated:** 2025-12-17 16:00 PST
**Upwork Job:** Météo France API weather data extraction and visualization for Martinique
**Client:** Remi (amateur weather enthusiast, passionate about Martinique)
**Status:** IN PROGRESS - SMS Alert System Integrated, Awaiting Proposal Acceptance
**Price:** $50 agreed (+ excellent review + future work commitment)
**Version:** 1.1

---

## Quick Context for New Sessions

Weather data extraction and visualization system for Martinique using Météo France API. Now includes full SMS alert subscription system with Twilio integration.

### Latest Update (2025-12-17 16:00)

**SMS Alert System Integration Complete**

Remi sent `alerte.rar` containing `alerte.html` - a UI mockup for SMS weather alert subscriptions. Full backend integration completed:

- FastAPI REST API for OTP verification and subscription management
- Twilio SMS service with profile-based alert templates
- SQLite database for subscriber storage
- Alert broadcaster connected to vigilance scheduler
- Frontend connected to real API endpoints (replacing simulated demo)

**Message sent to Remi (French):**
> Merci pour alerte.html! J'ai intégré le système complet: backend FastAPI avec endpoints OTP/subscription, service SMS Twilio avec templates par profil, SQLite pour les abonnés, et broadcaster connecté au scheduler vigilance. Le frontend est maintenant connecté aux vrais endpoints API au lieu des simulations. Il suffit de configurer les credentials Twilio dans .env et lancer `python main.py api`. N'oublie pas d'accepter la proposition! Des customisations souhaitées (pricing, phénomènes, templates SMS)?

**Pending:** Awaiting Remy to accept proposal and provide Twilio credentials or preferences.

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

1. **Awaiting Remi** - Accept Upwork proposal
2. **Twilio Setup** - Remi needs to create Twilio account and provide credentials
3. **Customization** - Any changes to pricing, phenomena, SMS templates?
4. **Deployment** - Deploy API to Render.com or o2switch
5. **Testing** - End-to-end testing with real phone numbers

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

---

**Author**: Vafa Bayat
**Contact**: vafa@bitscopic.com
