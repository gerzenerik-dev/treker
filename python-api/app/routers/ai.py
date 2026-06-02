import json
import os
import re

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/ai", tags=["ai"])

_PROMPTS = {
    "debts": (
        "Напиши одну мудрую и мотивирующую цитату на русском языке об управлении долгами"
        " и финансовой дисциплине. Только цитата и автор, формат JSON: "
        '{\"text\": \"...\", \"author\": \"...\"}'
    ),
    "saving": (
        "Напиши одну мотивирующую цитату на русском языке об экономии денег и разумных тратах."
        " Только цитата и автор, формат JSON: "
        '{\"text\": \"...\", \"author\": \"...\"}'
    ),
    "success": (
        "Напиши одну вдохновляющую цитату на русском языке о финансовом успехе и богатстве."
        " Только цитата и автор, формат JSON: "
        '{\"text\": \"...\", \"author\": \"...\"}'
    ),
    "general": (
        "Напиши одну мудрую цитату на русском языке о деньгах и финансовой мудрости."
        " Только цитата и автор, формат JSON: "
        '{\"text\": \"...\", \"author\": \"...\"}'
    ),
}


class QuoteRequest(BaseModel):
    context: str = "general"  # "debts" | "saving" | "success" | "general"


class QuoteResponse(BaseModel):
    text: str
    author: str


@router.post("/quote", response_model=QuoteResponse)
async def get_quote(
    req: QuoteRequest,
    _current_user: User = Depends(get_current_user),
) -> QuoteResponse:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="AI unavailable")

    prompt = _PROMPTS.get(req.context, _PROMPTS["general"])

    async with httpx.AsyncClient(timeout=8.0) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 150,
                "messages": [{"role": "user", "content": prompt}],
            },
        )

    if not resp.is_success:
        raise HTTPException(status_code=502, detail="AI request failed")

    raw = resp.json()["content"][0]["text"].strip()

    # Extract JSON object from response
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            return QuoteResponse(
                text=str(data.get("text", raw)),
                author=str(data.get("author", "")),
            )
        except (json.JSONDecodeError, KeyError):
            pass

    # Fallback: return raw text with empty author
    return QuoteResponse(text=raw, author="")
