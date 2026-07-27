# Architecture

## Overview

TetherFit Phase 5 (Polish & Growth) adds recurring sessions, trainer availability, realtime chat WebSockets, push subscription storage, automation campaigns, billing discounts/refunds/memberships, Prometheus metrics, and Kubernetes manifests.

## Phase 5 modules

| Module | API | Notes |
|--------|-----|-------|
| Scheduling | `/api/v1/recurrence-rules`, `/availability` | Weekly/biweekly series + Mon–Sun slots |
| Automations | `/api/v1/automations/campaigns` | renewal / birthday / announcement |
| Realtime | `/api/v1/ws/chat/{id}`, `/push/*` | WebSocket fan-out + VAPID stub |
| Billing polish | discounts on invoices, `/payments/{id}/refund`, `/memberships` | |
| Metrics | `GET /metrics` | Prometheus text format |

## Surfaces

| Path | Role |
|------|------|
| `/app/scheduling` | Trainer recurring + availability |
| `/app/automations` | Campaigns + push opt-in |
| `/app/chat` | REST + WebSocket live updates |
| `/client/*` | Client portal (Phase 4) |
| `/admin/*` | Platform admin (Phase 4) |

## Ops

- K8s templates: `infrastructure/k8s/tetherfit.yaml`
- Celery beat: session reminders hourly + daily automations
- Rate limit + request IDs unchanged from Phase 4

## Migration

`0006_phase5` — recurrence_rules, trainer_availability, push_subscriptions, automation_campaigns, memberships, invoice.discount_paise, payment refund fields, client.date_of_birth, pt_sessions.recurrence_rule_id
