# Architecture

## Overview

TetherFit Phase 6 (Production Completeness) adds session pause/resume, calendar drag-drop reschedule, assessment transformation photos via R2, SMTP email notifications, Razorpay webhooks, demo seed data, and Playwright public smoke tests.

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
| `/app/calendar` | Drag-drop reschedule (day/week) |
| `/app/sessions/:id` | Pause / resume |
| `/app/clients/:id` assessments | Metrics + photo upload |
| `/client/progress` | Photo thumbnails |
| `/`, `/features`, `/marketplace` | Public marketing (Playwright) |

## Ops

- K8s templates: `infrastructure/k8s/tetherfit.yaml`
- Celery beat: session reminders + automations (use notification provider)
- Rate limit applies to webhook by IP (no auth)

## Migration

`0007_phase6` — `pt_sessions.paused_at`
