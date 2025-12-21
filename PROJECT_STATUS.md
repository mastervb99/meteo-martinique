# Project Status: Martinique Weather Dashboard

**Last Updated:** 2025-12-20
**Upwork Job:** Météo France API weather data extraction and visualization for Martinique
**Client:** Remi
**Status:** DEPLOYED - Full Weather Dashboard + SMS/Email Alerts + Embedded Stripe Payments
**Version:** 2.3

---

## Quick Context

Weather data extraction, visualization, and alert notification system for Martinique using Météo France API. Includes full weather dashboard, separate SMS/Email subscription pages with embedded Stripe payment (no redirect), and Brevo integration for notifications.

### Live URLs

- **Production:** https://meteo-martinique.onrender.com
- **GitHub:** https://github.com/mastervb99/meteo-martinique

---

## Current Status (2025-12-20)

### Completed Features

| Feature | Status | Notes |
|---------|--------|-------|
| Weather Dashboard | LIVE | 4 pages: Aujourd'hui, Prévisions, Cartes, Alertes |
| SMS Subscription Page | LIVE | Separate page with embedded Stripe payment |
| Email Subscription Page | LIVE | Separate page with embedded Stripe payment |
| Embedded Stripe Payment | LIVE | Payment form on page, no redirect |
| SMS Alerts (Brevo) | LIVE | Brevo API configured |
| Email Alerts (Brevo) | LIVE | Same Brevo integration |
| Interactive Maps | LIVE | Vigilance, Forecast, Rain maps |
| Weather Charts | LIVE | Temperature, City Comparison, Hourly |
| Demo Data Generator | LIVE | /api/generate/demo endpoint |

### Pages

| Page | Route | Description |
|------|-------|-------------|
| Alertes (Landing) | `/` | Plan selection - links to SMS/Email pages |
| Alertes SMS | `/alerte-sms` | Phone input + embedded Stripe payment (€4.99/mo) |
| Alertes Email | `/alerte-email` | Email input + embedded Stripe payment (€10/yr) |
| Aujourd'hui | `/aujourd-hui` | Today's weather for all cities |
| Prévisions | `/previsions` | 7-day forecast with charts |
| Cartes | `/cartes` | Interactive maps + charts |
| Success | `/success` | Payment confirmation page |

---

## Recent Changes

### 2025-12-20: Separate SMS/Email Pages + Embedded Stripe Payment

1. **Separate subscription pages** - SMS and Email now have dedicated pages
   - `/alerte-sms` - Phone number + profile + embedded payment
   - `/alerte-email` - Email address + profile + embedded payment
2. **Embedded Stripe Payment** - Payment form directly on page using Stripe Elements
   - No more redirect to Stripe Checkout
   - PaymentIntent API for secure embedded payment
3. **Landing page redesign** - Main `/` page shows two plan cards linking to subscription pages
4. **New API endpoints**:
   - `POST /api/stripe/create-payment-intent` - Create PaymentIntent for embedded form
   - `POST /api/stripe/confirm-payment` - Confirm payment and activate subscription

### 2025-12-19: Stripe Payment Integration

1. Added Stripe payment processing for subscriptions
2. Two pricing tiers: SMS €4.99/month, Email €10/year
3. Webhook support for payment events

### 2025-12-18: Brevo Integration + Dashboard Pages

1. Replaced Twilio with Brevo for SMS + Email
2. Removed OTP verification - Direct subscription flow
3. Added weather dashboard pages (Aujourd'hui, Prévisions, Cartes)
4. Fixed chart legend overlap and hourly data generation

### Environment Variables Required

```
BREVO_API_KEY=xsmtpsib-...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_... (optional)
```

---

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Frontend       │────▶│  FastAPI     │────▶│  Brevo          │
│  (HTML + JS)    │     │  (api.py)    │     │  (SMS + Email)  │
└─────────────────┘     └──────────────┘     └─────────────────┘
        │                      │
        │              ┌───────┼───────────────┐
        │              ▼       ▼               ▼
        │        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │        │ SQLite   │ │ Maps     │ │ Charts   │
        │        │ (subs)   │ │ (Folium) │ │ (Plotly) │
        │        └──────────┘ └──────────┘ └──────────┘
        │
        └──────▶ Stripe Elements (Embedded Payment)
                        │
                        ▼
                 ┌──────────────┐
                 │ Stripe API   │
                 │ (PaymentIntent)│
                 └──────────────┘
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
| `/api/stripe/create-payment-intent` | POST | Create PaymentIntent (embedded) |
| `/api/stripe/confirm-payment` | POST | Confirm payment + activate subscription |
| `/api/stripe/checkout` | POST | Create checkout session (legacy redirect) |
| `/api/stripe/verify/{session_id}` | GET | Verify checkout session |
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
├── stripe_service.py      # Stripe payment (PaymentIntent + Checkout)
├── subscriptions.py       # SQLite subscription management
├── alert_broadcaster.py   # Alert broadcasting
├── weather_extractor.py   # Météo France API
├── map_generator.py       # Folium maps
├── chart_generator.py     # Plotly charts
├── scheduler.py           # Automated updates
├── static/
│   ├── alerte.html        # Landing page with plan selection
│   ├── alerte-sms.html    # SMS subscription + embedded payment
│   ├── alerte-email.html  # Email subscription + embedded payment
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

## Subscription Flow

### SMS Subscription (€4.99/month)
1. User visits `/alerte-sms`
2. Enters phone number, email (for invoice), and profile
3. Stripe Payment Element loads automatically
4. User enters card details and clicks "Payer"
5. Payment processed via PaymentIntent (no redirect)
6. Subscription created, welcome SMS sent

### Email Subscription (€10/year)
1. User visits `/alerte-email`
2. Enters email address and profile
3. Stripe Payment Element loads automatically
4. User enters card details and clicks "Payer"
5. Payment processed via PaymentIntent (no redirect)
6. Subscription created, welcome email sent

---

## Client Communication Summary

| Date | Event |
|------|-------|
| 2025-12-16 | Initial contact, demo sent |
| 2025-12-17 | SMS mockup received, backend built, deployed to Render |
| 2025-12-18 | Brevo integration, OTP removed, dashboard pages added |
| 2025-12-19 | Stripe payment integration (SMS €4.99/mo, Email €10/yr) |
| 2025-12-20 | Separate SMS/Email pages, embedded Stripe payment (no redirect) |

---

**Author**: Vafa Bayat
