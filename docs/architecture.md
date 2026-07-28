# Architecture

## Overview

TetherFit Phase 7 (Solo Trainer CRM) adds client roster CRM fields and actions, geolocation on session start, cash/UPI QR collection, GST invoice HTML, and a settings hub for business/GST/UPI/availability.

## Phase 7 modules

| Module | API / surface | Notes |
|--------|---------------|-------|
| Client CRM | `ClientOut` aggregates + PT dates | Joined, paid, completed, `pt_start_at`/`pt_end_at` |
| Client actions | Web client detail | Schedule recurrence, cancel upcoming, GST invoice |
| Geo start | `POST /sessions/{id}/start` + `StartSessionBody` | Persists `start_latitude/longitude/accuracy_m` |
| Cash pay | `POST /payments/cash` | Immediate success + invoice paid |
| UPI QR | `GET /invoices/{id}/upi-qr` | Uses org `upi_vpa` |
| GST invoice | `GET /invoices/{id}/gst-invoice` | Printable HTML; tax from `default_gst_pct` |
| Settings hub | `PATCH /organizations/me` | Business address/phone, GSTIN, UPI, GST % + availability |

## Phase 6 modules

| Module | API / surface | Notes |
|--------|---------------|-------|
| Session pause | `POST /sessions/{id}/pause`, `/resume` | `in_progress` ↔ `paused`; `paused_at` |
| Calendar DnD | Web calendar day/week | HTML5 drag → `PATCH /sessions/{id}` |
| Transformation photos | media presign + assessments `photo_urls` | Trainer client assessments + portal progress |
| SMTP | `SmtpEmailProvider` when `SMTP_HOST` set | Noop fallback otherwise |
| Razorpay webhook | `POST /api/v1/payments/webhook/razorpay` | HMAC `X-Razorpay-Signature` |
| Seed / e2e | `scripts/seed_demo.py`, Playwright smoke | CI public + health only |

## Surfaces

| Path | Role |
|------|------|
| `/app/clients` | Roster with PT / paid / completed |
| `/app/clients/:id` | Schedule, cancel, invoice |
| `/app/sessions/:id` | GPS capture on start; pause / resume |
| `/app/payments` | Cash, UPI QR, GST invoice |
| `/app/settings` | Business, GST, UPI, availability |
| `/app/calendar` | Drag-drop reschedule (day/week) |
| `/`, `/features`, `/marketplace` | Public marketing (Playwright) |

## Ops

- K8s templates: `infrastructure/k8s/tetherfit.yaml`
- Celery beat: session reminders + automations (use notification provider)
- Rate limit applies to webhook by IP (no auth)

## Migration

`0008_phase7` — clients PT dates; org business/UPI/GST; session start geo  
`0007_phase6` — `pt_sessions.paused_at`
