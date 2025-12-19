# Martinique Weather Dashboard

Weather data extraction, visualization, and alert notification system for Martinique using Météo France API. Includes full weather dashboard with interactive maps, charts, SMS/Email subscription system via Brevo, and Stripe payment processing.

## Live Demo

- **Production:** https://meteo-martinique.onrender.com
- **GitHub:** https://github.com/mastervb99/meteo-martinique

## Features

**Weather Dashboard (4 Pages)**
- Aujourd'hui: Current weather for all 10 Martinique cities
- Prévisions: 7-day forecast with temperature charts
- Cartes: Interactive maps (vigilance, forecast, rain) and comparison charts
- Alertes: SMS/Email subscription for weather alerts

**Interactive Maps (Folium)**
- Vigilance map with color-coded alert overlays
- Forecast map with city markers and weather popups
- Precipitation heatmap

**Charts & Dashboards (Plotly)**
- Multi-city temperature comparison (min/max over 7 days)
- Hourly dashboard with temperature, precipitation, and wind panels
- City comparison bar charts
- Vigilance gauge indicator

**Alert Notifications (Brevo)**
- SMS alerts via Brevo API
- Email alerts via Brevo API
- 4 subscriber profiles (Plaisancier, Agriculteur, Entreprise, Grand Public)
- Direct subscription (no OTP verification)

**Payment Processing (Stripe)**
- SMS subscription: €4.99/month
- Email subscription: €10/year
- Secure Stripe Checkout hosted payment page
- Webhook support for payment events

## Quick Start

### Local Development

```bash
# Clone and setup
git clone https://github.com/mastervb99/meteo-martinique.git
cd martinique_weather
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Brevo API key

# Run API server
python api.py
# Open http://localhost:8000
```

### Deploy to Render.com

1. Fork/push to GitHub
2. Create new Web Service on Render
3. Connect GitHub repo
4. Add environment variables:
   - `BREVO_API_KEY=your_key`
   - `STRIPE_SECRET_KEY=sk_live_...`
5. Deploy

## Configuration

```bash
# .env file

# Brevo (SMS + Email) - Required
BREVO_API_KEY=your_brevo_api_key
BREVO_SENDER_EMAIL=alertes@meteo-martinique.fr
BREVO_SENDER_NAME=Meteo Martinique
BREVO_SMS_SENDER=MeteoMQ

# Stripe (Payments) - Required for subscriptions
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...  # Optional

# Météo France - Optional (for live data)
METEO_FRANCE_APP_ID=your_app_id
METEO_FRANCE_API_KEY=your_api_key
```

## API Endpoints

### Weather Data
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/weather/current` | GET | Current weather all cities |
| `/api/weather/forecast/{city}` | GET | 7-day forecast for city |
| `/api/weather/hourly/{city}` | GET | 48-hour hourly forecast |
| `/api/weather/vigilance` | GET | Current vigilance alerts |
| `/api/cities` | GET | List of Martinique cities |

### Maps & Charts
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/maps/vigilance` | GET | Vigilance map HTML |
| `/api/maps/forecast` | GET | Forecast map HTML |
| `/api/maps/rain` | GET | Precipitation map HTML |
| `/api/charts/temperature` | GET | Temperature chart HTML |
| `/api/charts/comparison` | GET | City comparison chart |
| `/api/charts/hourly/{city}` | GET | Hourly dashboard chart |

### Subscriptions
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/subscribe` | POST | Subscribe (direct, no OTP) |
| `/api/subscribe/test` | POST | Send test alert |
| `/api/subscribe/{ref}` | GET | Get subscription details |
| `/api/subscribe/unsubscribe` | DELETE | Unsubscribe |

### Payments (Stripe)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/stripe/config` | GET | Get pricing info |
| `/api/stripe/checkout` | POST | Create checkout session |
| `/api/stripe/verify/{session_id}` | GET | Verify payment |
| `/api/stripe/webhook` | POST | Handle Stripe webhooks |
| `/api/stripe/status` | GET | Check subscription status |

### Utility
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/generate/demo` | POST | Generate demo data |

## Project Structure

```
martinique_weather/
├── api.py                 # FastAPI REST API (main entry)
├── main.py                # CLI entry point
├── config.py              # Configuration
├── brevo_service.py       # Brevo SMS + Email
├── stripe_service.py      # Stripe payment processing
├── subscriptions.py       # SQLite subscription management
├── alert_broadcaster.py   # Alert broadcasting
├── weather_extractor.py   # Météo France API
├── map_generator.py       # Folium maps
├── chart_generator.py     # Plotly charts
├── scheduler.py           # Automated updates
├── static/
│   ├── alerte.html        # Subscription page (/)
│   ├── aujourdhui.html    # Today's weather
│   ├── previsions.html    # 7-day forecast
│   ├── cartes.html        # Maps page
│   └── success.html       # Payment success page
├── requirements.txt
├── .env.example
├── Dockerfile
└── docker-compose.yml
```

## CLI Commands

```bash
python main.py demo          # Generate demo data
python main.py extract       # Extract live data (needs API key)
python main.py schedule      # Start automated updates
python main.py info          # Show system info
```

## Docker

```bash
docker-compose up -d martinique-weather
docker-compose logs -f martinique-weather
```

## Dependencies

| Package | Purpose |
|---------|---------|
| fastapi | REST API framework |
| uvicorn | ASGI server |
| sib-api-v3-sdk | Brevo SMS/Email |
| stripe | Payment processing |
| folium | Interactive maps |
| plotly | Charts and dashboards |
| pandas | Data processing |
| meteofrance-api | Météo France API client |

---

**Version:** 2.2
**Author:** Vafa Bayat
**Last Updated:** 2025-12-19
