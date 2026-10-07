from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from app.core.config import Settings, get_settings


@dataclass
class AiCompletion:
    provider: str
    model: str
    content: dict[str, Any]
    raw_text: str
    tokens_in: int = 0
    tokens_out: int = 0


class AiProvider(ABC):
    name: str

    @abstractmethod
    def complete(self, system: str, user: str, *, model: str | None = None) -> AiCompletion: ...


class NoopAiProvider(AiProvider):
    name = "noop"

    def complete(self, system: str, user: str, *, model: str | None = None) -> AiCompletion:
        feature = "generic"
        lower = user.lower()
        if "workout" in lower or "exercise" in lower:
            feature = "workout"
            content = {
                "title": "Full Body Strength",
                "duration_min": 45,
                "items": [
                    {"name": "Goblet Squat", "sets": 3, "reps": "10", "rest_sec": 60},
                    {"name": "Push-up", "sets": 3, "reps": "12", "rest_sec": 45},
                    {"name": "Dumbbell Row", "sets": 3, "reps": "10/side", "rest_sec": 60},
                    {"name": "Plank", "sets": 3, "reps": "40s", "rest_sec": 30},
                ],
                "notes": "Generated locally (noop AI). Swap AI_PROVIDER for live models.",
            }
        elif "meal" in lower or "diet" in lower or "nutrition" in lower:
            feature = "diet"
            content = {
                "name": "Balanced 2200 kcal day",
                "calories": 2200,
                "protein_g": 140,
                "carbs_g": 220,
                "fat_g": 70,
                "meals": [
                    {"name": "Breakfast", "items": ["Oats + whey", "Banana"]},
                    {"name": "Lunch", "items": ["Chicken rice bowl", "Salad"]},
                    {"name": "Dinner", "items": ["Paneer stir-fry", "Quinoa"]},
                ],
            }
        elif "summary" in lower or "session" in lower:
            feature = "session_summary"
            content = {
                "summary": (
                    "Solid session with good adherence. " "Focus next time on progressive overload."
                ),
                "highlights": ["Completed all sets", "RPE ~7"],
                "next_focus": ["Add 2.5kg to primary lifts", "Hip mobility"],
            }
        elif "insight" in lower or "revenue" in lower or "retention" in lower:
            feature = "insights"
            content = {
                "insights": [
                    "Session completion looks healthy — protect Friday slots from no-shows.",
                    "Low-credit clients are a renewal opportunity this week.",
                    "Package attach rate can improve with a 12-session promo.",
                ],
                "actions": ["Message low-credit clients", "Publish marketplace listing"],
            }
        else:
            content = {
                "reply": (
                    "I'm your Coach Copilot (noop). Ask for a workout, meal plan, "
                    "session summary, or business insights."
                ),
                "suggestions": [
                    "Generate a 4-day hypertrophy plan",
                    "Draft a renewal message",
                    "Summarize today's sessions",
                ],
            }
        raw = json.dumps(content)
        return AiCompletion(
            provider=self.name,
            model=model or f"noop-{feature}",
            content=content,
            raw_text=raw,
            tokens_in=max(1, len(system + user) // 4),
            tokens_out=max(1, len(raw) // 4),
        )


class OpenAiCompatibleProvider(AiProvider):
    """Works with OpenAI, Azure OpenAI-compatible, Groq, Ollama (/v1), etc."""

    name = "openai_compatible"

    def __init__(self, api_key: str, base_url: str, default_model: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model

    def complete(self, system: str, user: str, *, model: str | None = None) -> AiCompletion:
        import urllib.error
        import urllib.request

        use_model = model or self.default_model
        payload = {
            "model": use_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.4,
        }
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode())
        except urllib.error.URLError, TimeoutError, json.JSONDecodeError:
            return NoopAiProvider().complete(system, user, model=use_model)

        text = (
            data.get("choices", [{}])[0].get("message", {}).get("content")
            or data.get("choices", [{}])[0].get("text")
            or "{}"
        )
        usage = data.get("usage") or {}
        content = _parse_jsonish(text)
        return AiCompletion(
            provider=self.name,
            model=use_model,
            content=content,
            raw_text=text,
            tokens_in=int(usage.get("prompt_tokens") or 0),
            tokens_out=int(usage.get("completion_tokens") or 0),
        )


def _parse_jsonish(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {"reply": text, "data": parsed}
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass
        return {"reply": text}


def get_ai_provider(settings: Settings | None = None) -> AiProvider:
    settings = settings or get_settings()
    provider = (settings.ai_provider or "noop").lower()
    if provider in {"openai", "openai_compatible", "ollama", "gemini", "claude"}:
        if settings.ai_api_key or provider == "ollama":
            return OpenAiCompatibleProvider(
                api_key=settings.ai_api_key or "ollama",
                base_url=settings.ai_base_url
                or (
                    "http://localhost:11434/v1"
                    if provider == "ollama"
                    else "https://api.openai.com/v1"
                ),
                default_model=settings.ai_model or "gpt-4o-mini",
            )
    return NoopAiProvider()
