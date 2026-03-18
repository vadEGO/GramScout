from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import uuid

from app.core.database import get_db
from app.core.security import encrypt, decrypt
from app.core.logging import logger
from app.models.llm_config import LLMProvider, LLMModelConfig, TroubleshootSession

router = APIRouter(tags=["llm-config"])

# ─── AVAILABLE MODELS CATALOG ──────────────────────────────────

MODEL_CATALOG = {
    "openrouter": [
        {
            "id": "openai/gpt-4o-mini",
            "name": "GPT-4o Mini",
            "cost_in": 0.15,
            "cost_out": 0.60,
            "quality": 7.5,
            "speed": 9.0,
            "max_tokens": 16384,
            "functions": True,
        },
        {
            "id": "openai/gpt-4o",
            "name": "GPT-4o",
            "cost_in": 2.50,
            "cost_out": 10.0,
            "quality": 9.5,
            "speed": 7.0,
            "max_tokens": 16384,
            "functions": True,
        },
        {
            "id": "anthropic/claude-sonnet-4",
            "name": "Claude Sonnet 4",
            "cost_in": 3.0,
            "cost_out": 15.0,
            "quality": 9.5,
            "speed": 6.5,
            "max_tokens": 16384,
            "functions": True,
        },
        {
            "id": "anthropic/claude-3.5-haiku",
            "name": "Claude 3.5 Haiku",
            "cost_in": 0.80,
            "cost_out": 4.0,
            "quality": 8.0,
            "speed": 9.5,
            "max_tokens": 8192,
            "functions": True,
        },
        {
            "id": "google/gemini-2.0-flash",
            "name": "Gemini 2.0 Flash",
            "cost_in": 0.10,
            "cost_out": 0.40,
            "quality": 7.0,
            "speed": 9.5,
            "max_tokens": 8192,
            "functions": False,
        },
        {
            "id": "google/gemini-2.5-flash",
            "name": "Gemini 2.5 Flash",
            "cost_in": 0.15,
            "cost_out": 0.60,
            "quality": 8.0,
            "speed": 9.0,
            "max_tokens": 8192,
            "functions": False,
        },
        {
            "id": "deepseek/deepseek-chat-v3",
            "name": "DeepSeek Chat V3",
            "cost_in": 0.14,
            "cost_out": 0.28,
            "quality": 7.5,
            "speed": 8.0,
            "max_tokens": 8192,
            "functions": False,
        },
        {
            "id": "meta-llama/llama-3.1-8b-instruct",
            "name": "Llama 3.1 8B",
            "cost_in": 0.02,
            "cost_out": 0.04,
            "quality": 5.0,
            "speed": 9.5,
            "max_tokens": 8192,
            "functions": False,
        },
        {
            "id": "mistralai/mistral-7b-instruct",
            "name": "Mistral 7B",
            "cost_in": 0.03,
            "cost_out": 0.05,
            "quality": 5.5,
            "speed": 9.5,
            "max_tokens": 8192,
            "functions": False,
        },
    ],
    "openai": [
        {
            "id": "gpt-4o-mini",
            "name": "GPT-4o Mini",
            "cost_in": 0.15,
            "cost_out": 0.60,
            "quality": 7.5,
            "speed": 9.0,
            "max_tokens": 16384,
            "functions": True,
        },
        {
            "id": "gpt-4o",
            "name": "GPT-4o",
            "cost_in": 2.50,
            "cost_out": 10.0,
            "quality": 9.5,
            "speed": 7.0,
            "max_tokens": 16384,
            "functions": True,
        },
        {
            "id": "gpt-4.1-mini",
            "name": "GPT-4.1 Mini",
            "cost_in": 0.40,
            "cost_out": 1.60,
            "quality": 8.0,
            "speed": 9.0,
            "max_tokens": 1047576,
            "functions": True,
        },
    ],
    "anthropic": [
        {
            "id": "claude-sonnet-4-20250514",
            "name": "Claude Sonnet 4",
            "cost_in": 3.0,
            "cost_out": 15.0,
            "quality": 9.5,
            "speed": 6.5,
            "max_tokens": 16384,
            "functions": True,
        },
        {
            "id": "claude-3-5-haiku-20241022",
            "name": "Claude 3.5 Haiku",
            "cost_in": 0.80,
            "cost_out": 4.0,
            "quality": 8.0,
            "speed": 9.5,
            "max_tokens": 8192,
            "functions": True,
        },
    ],
    "google": [
        {
            "id": "gemini-2.0-flash",
            "name": "Gemini 2.0 Flash",
            "cost_in": 0.10,
            "cost_out": 0.40,
            "quality": 7.0,
            "speed": 9.5,
            "max_tokens": 8192,
            "functions": False,
        },
    ],
}

ROLE_ASSIGNMENTS = {
    "commenting": {
        "preferred": "openai/gpt-4o-mini",
        "fallback": "google/gemini-2.0-flash",
    },
    "dialogue": {
        "preferred": "openai/gpt-4o-mini",
        "fallback": "anthropic/claude-3.5-haiku",
    },
    "analysis": {"preferred": "openai/gpt-4o", "fallback": "anthropic/claude-sonnet-4"},
    "troubleshoot": {
        "preferred": "openai/gpt-4o",
        "fallback": "anthropic/claude-sonnet-4",
    },
    "general": {
        "preferred": "openai/gpt-4o-mini",
        "fallback": "deepseek/deepseek-chat-v3",
    },
}


# ─── PROVIDERS ────────────────────────────────────────────────


@router.get("/llm/providers")
async def list_providers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LLMProvider).order_by(LLMProvider.priority.asc()))
    providers = list(result.scalars().all())
    return [
        {
            "id": p.id,
            "name": p.name,
            "type": p.provider_type,
            "active": p.is_active,
            "priority": p.priority,
            "daily_limit": p.daily_limit_usd,
            "daily_spend": p.daily_spend_usd,
            "total_spend": p.total_spend_usd,
            "has_api_key": bool(p.api_key_encrypted),
        }
        for p in providers
    ]


@router.post("/llm/providers")
async def add_provider(
    name: str,
    provider_type: str,
    api_key: str = "",
    base_url: str = "",
    priority: int = 5,
    daily_limit_usd: float = 10.0,
    db: AsyncSession = Depends(get_db),
):
    provider = LLMProvider(
        id=str(uuid.uuid4()),
        name=name,
        provider_type=provider_type,
        api_key_encrypted=encrypt(api_key) if api_key else None,
        base_url=base_url or None,
        priority=priority,
        daily_limit_usd=daily_limit_usd,
    )
    db.add(provider)
    await db.commit()
    return {"id": provider.id, "name": provider.name, "type": provider_type}


@router.put("/llm/providers/{provider_id}")
async def update_provider(
    provider_id: str,
    api_key: str = "",
    daily_limit_usd: float = 0,
    is_active: bool = True,
    db: AsyncSession = Depends(get_db),
):
    provider = await db.get(LLMProvider, provider_id)
    if not provider:
        raise HTTPException(404, "Provider not found")
    if api_key:
        provider.api_key_encrypted = encrypt(api_key)
    if daily_limit_usd > 0:
        provider.daily_limit_usd = daily_limit_usd
    provider.is_active = is_active
    await db.commit()
    return {"updated": True}


@router.delete("/llm/providers/{provider_id}")
async def delete_provider(provider_id: str, db: AsyncSession = Depends(get_db)):
    provider = await db.get(LLMProvider, provider_id)
    if not provider:
        raise HTTPException(404, "Provider not found")
    await db.delete(provider)
    await db.commit()
    return {"deleted": True}


# ─── MODEL CATALOG ────────────────────────────────────────────


@router.get("/llm/models")
async def list_models():
    """List all available models across all providers."""
    models = []
    for provider_type, provider_models in MODEL_CATALOG.items():
        for m in provider_models:
            models.append(
                {
                    "id": f"{provider_type}/{m['id']}"
                    if "/" not in m["id"]
                    else m["id"],
                    "display_name": m["name"],
                    "provider": provider_type,
                    "cost_per_1m_input": m["cost_in"],
                    "cost_per_1m_output": m["cost_out"],
                    "quality_score": m["quality"],
                    "speed_score": m["speed"],
                    "max_tokens": m["max_tokens"],
                    "supports_functions": m["functions"],
                }
            )
    return models


@router.get("/llm/models/roles")
async def get_role_assignments():
    """Get model assignments for each role."""
    return ROLE_ASSIGNMENTS


@router.put("/llm/models/roles")
async def update_role_assignment(
    role: str,
    preferred_model: str,
    fallback_model: str = "",
):
    """Update which model is used for a specific role."""
    if role not in ROLE_ASSIGNMENTS:
        raise HTTPException(
            400, f"Invalid role. Choose from: {list(ROLE_ASSIGNMENTS.keys())}"
        )
    ROLE_ASSIGNMENTS[role] = {
        "preferred": preferred_model,
        "fallback": fallback_model or ROLE_ASSIGNMENTS[role].get("fallback", ""),
    }
    return {"updated": True, "role": role, "preferred": preferred_model}


# ─── USAGE STATS ──────────────────────────────────────────────


@router.get("/llm/usage")
async def get_usage(db: AsyncSession = Depends(get_db)):
    """Get LLM usage statistics."""
    providers = list((await db.execute(select(LLMProvider))).scalars().all())
    models = list((await db.execute(select(LLMModelConfig))).scalars().all())

    total_spend = sum(p.total_spend_usd for p in providers)
    daily_spend = sum(p.daily_spend_usd for p in providers)

    return {
        "total_spend_usd": round(total_spend, 4),
        "daily_spend_usd": round(daily_spend, 4),
        "providers": len([p for p in providers if p.is_active]),
        "models_configured": len(models),
        "role_assignments": ROLE_ASSIGNMENTS,
    }


# ─── TEST CONNECTION ─────────────────────────────────────────


@router.post("/llm/test")
async def test_provider(
    provider_type: str = "openrouter",
    api_key: str = "",
    model: str = "openai/gpt-4o-mini",
):
    """Test an LLM provider connection with a simple prompt."""
    from app.ai.llm_client import OpenRouterClient

    try:
        client = OpenRouterClient(api_key=api_key) if api_key else None
        if not client or not client.api_key:
            return {"success": False, "error": "No API key provided"}

        result = await client.chat_completion(
            messages=[{"role": "user", "content": "Say 'hello' in one word"}],
            model=model,
            temperature=0.1,
            max_tokens=10,
        )
        await client.close()

        if result:
            return {"success": True, "response": result.strip(), "model": model}
        return {"success": False, "error": "No response from model"}

    except Exception as e:
        return {"success": False, "error": str(e)}
