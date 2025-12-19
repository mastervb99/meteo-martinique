# Project Status: Martinique Weather Dashboard

**Last Updated:** 2025-12-19
**Upwork Job:** Météo France API weather data extraction and visualization for Martinique
**Client:** Remi
**Status:** DEPLOYED - Full Weather Dashboard + SMS/Email Alerts + Stripe Payments
**Version:** 2.2

---

## Quick Context

Weather data extraction, visualization, and alert notification system for Martinique using Météo France API. Includes full weather dashboard, SMS/Email subscription system with Brevo integration, and Stripe payment processing for subscriptions.

### Live URLs

- **Production:** https://meteo-martinique.onrender.com
- **GitHub:** https://github.com/mastervb99/meteo-martinique

---

## Current Status (2025-12-18)

### Completed Features

| Feature | Status | Notes |
|---------|--------|-------|
| Weather Dashboard | LIVE | 4 pages: Aujourd'hui, Prévisions, Cartes, Alertes |
| SMS Alerts (Brevo) | LIVE | Brevo API key configured |
| Email Alerts (Brevo) | LIVE | Same Brevo integration |
| Subscription Flow | LIVE | Simplified (no OTP) |
| Interactive Maps | LIVE | Vigilance, Forecast, Rain maps |
| Weather Charts | LIVE | Temperature, City Comparison, Hourly |
| Demo Data Generator | LIVE | /api/generate/demo endpoint |
| Stripe Payments | LIVE | SMS €4.99/mo, Email €10/yr |

### Pages

| Page | Route | Description |
|------|-------|-------------|
| Aujourd'hui | `/aujourd-hui` | Today's weather for all cities |
| Prévisions | `/previsions` | 7-day forecast with charts |
| Cartes | `/cartes` | Interactive maps + charts |
| Alertes | `/` | SMS/Email subscription |

---

## Recent Changes

### 2025-12-19: Stripe Payment Integration

1. **Added Stripe payment processing** for subscriptions
2. **Two pricing tiers**: SMS €4.99/month, Email €10/year
3. **Stripe Checkout integration** - Secure hosted payment page
4. **Payment success page** - Confirms subscription activation
5. **Webhook support** - Handles payment events

### 2025-12-18: Brevo Integration + OTP Removal

1. **Replaced Twilio with Brevo** for SMS + Email
2. **Removed OTP verification** - Direct subscription flow
3. **Added weather dashboard pages** (Aujourd'hui, Prévisions, Cartes)
4. **Fixed chart legend overlap** - Legends now below charts
5. **Fixed hourly data generation** - Now generates for all 10 cities
6. **Fixed accented city names** - Le François, Trinité work correctly

### Environment Variables Required

```
BREVO_API_KEY=xsmtpsib-...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_... (optional, for client-side)
STRIPE_WEBHOOK_SECRET=whsec_... (optional, for webhook verification)
```

---

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Frontend       │────▶│  FastAPI     │────▶│  Brevo          │
│  (HTML + JS)    │     │  (api.py)    │     │  (SMS + Email)  │
└─────────────────┘     └──────────────┘     └─────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌──────────┐   ┌──────────┐   ┌──────────────┐
        │ SQLite   │   │ Maps     │   │ Charts       │
        │ (subs)   │   │ (Folium) │   │ (Plotly)     │
        └──────────┘   └──────────┘   └──────────────┘
```

---

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
| `/api/charts/vigilance` | GET | Vigilance gauge chart |

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
| `/api/stripe/config` | GET | Get Stripe publishable key + prices |
| `/api/stripe/checkout` | POST | Create checkout session |
| `/api/stripe/verify/{session_id}` | GET | Verify payment |
| `/api/stripe/webhook` | POST | Handle Stripe webhooks |
| `/api/stripe/status` | GET | Check subscription status |

### Utility
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/generate/demo` | POST | Generate demo data |

---

## File Structure

```
martinique_weather/
├── main.py                # CLI entry point
├── api.py                 # FastAPI REST API
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

---

## Next Steps

### Awaiting Client Feedback

1. **Test SMS delivery** - Client to subscribe and verify SMS receipt
2. **Test Email delivery** - If using email notifications
3. **Review dashboard pages** - Feedback on design/functionality

### Potential Enhancements (If Requested)

1. **Real Météo France data** - Connect to live API (needs credentials)
2. **Automated scheduler** - CRON job for regular data updates
3. **WhatsApp integration** - Via Brevo if needed
4. **Custom domain** - Deploy to o2switch with client domain
5. **Admin panel** - View subscribers, send manual alerts

---

## Configuration

### Required Environment Variables

```bash
# Brevo (SMS + Email)
BREVO_API_KEY=your_brevo_api_key

# Optional: Météo France (for live data)
METEO_FRANCE_APP_ID=your_app_id
METEO_FRANCE_API_KEY=your_api_key
```

### Render.com Setup

1. Connect GitHub repo
2. Add BREVO_API_KEY in Environment
3. Deploy

---

## Client Communication Summary

| Date | Event |
|------|-------|
| 2025-12-16 | Initial contact, demo sent |
| 2025-12-17 | SMS mockup received, backend built, deployed to Render |
| 2025-12-18 | Brevo integration, OTP removed, dashboard pages added |

---

**Author**: Vafa Bayat
