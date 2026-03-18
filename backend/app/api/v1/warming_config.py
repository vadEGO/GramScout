from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.database import get_db
from app.models.warming_profile import WarmingProfile


router = APIRouter(prefix="/warming-config", tags=["warming-config"])


@router.get("/profiles")
async def list_profiles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WarmingProfile).where(WarmingProfile.is_active == True)
    )
    profiles = list(result.scalars().all())
    if not profiles:
        # Create default profile
        default = WarmingProfile(id=str(uuid.uuid4()), name="Default", is_default=True)
        db.add(default)
        await db.commit()
        await db.refresh(default)
        profiles = [default]
    return [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "is_default": p.is_default,
            "initial_rest_hours_min": p.initial_rest_hours_min,
            "initial_rest_hours_max": p.initial_rest_hours_max,
            "action_weights": p.action_weights,
            "stages": p.stages,
            "delay_ranges": p.delay_ranges,
            "idle_probability": p.idle_probability,
            "idle_duration_min": p.idle_duration_min,
            "idle_duration_max": p.idle_duration_max,
            "action_order_randomization": p.action_order_randomization,
            "interleave_non_target_actions": p.interleave_non_target_actions,
            "typing_speed_variation": p.typing_speed_variation,
            "warming_channels": p.warming_channels,
            "stage_advance_probability": p.stage_advance_probability,
            "max_stage_advance_per_session": p.max_stage_advance_per_session,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in profiles
    ]


@router.get("/profiles/{profile_id}")
async def get_profile(profile_id: str, db: AsyncSession = Depends(get_db)):
    profile = await db.get(WarmingProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {
        "id": profile.id,
        "name": profile.name,
        "description": profile.description,
        "is_default": profile.is_default,
        "initial_rest_hours_min": profile.initial_rest_hours_min,
        "initial_rest_hours_max": profile.initial_rest_hours_max,
        "action_weights": profile.action_weights,
        "stages": profile.stages,
        "delay_ranges": profile.delay_ranges,
        "idle_probability": profile.idle_probability,
        "idle_duration_min": profile.idle_duration_min,
        "idle_duration_max": profile.idle_duration_max,
        "action_order_randomization": profile.action_order_randomization,
        "interleave_non_target_actions": profile.interleave_non_target_actions,
        "typing_speed_variation": profile.typing_speed_variation,
        "warming_channels": profile.warming_channels,
        "stage_advance_probability": profile.stage_advance_probability,
        "max_stage_advance_per_session": profile.max_stage_advance_per_session,
    }


@router.post("/profiles")
async def create_profile(
    name: str,
    description: str = "",
    db: AsyncSession = Depends(get_db),
):
    profile = WarmingProfile(
        id=str(uuid.uuid4()),
        name=name,
        description=description,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return {"id": profile.id, "name": profile.name}


@router.put("/profiles/{profile_id}")
async def update_profile(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
    **updates,
):
    profile = await db.get(WarmingProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    allowed_fields = {
        "name",
        "description",
        "initial_rest_hours_min",
        "initial_rest_hours_max",
        "action_weights",
        "stages",
        "delay_ranges",
        "idle_probability",
        "idle_duration_min",
        "idle_duration_max",
        "action_order_randomization",
        "interleave_non_target_actions",
        "typing_speed_variation",
        "warming_channels",
        "stage_advance_probability",
        "max_stage_advance_per_session",
    }
    for key, value in updates.items():
        if key in allowed_fields and hasattr(profile, key):
            setattr(profile, key, value)
    await db.commit()
    return {"updated": True}


@router.delete("/profiles/{profile_id}")
async def delete_profile(profile_id: str, db: AsyncSession = Depends(get_db)):
    profile = await db.get(WarmingProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    if profile.is_default:
        raise HTTPException(status_code=400, detail="Cannot delete default profile")
    profile.is_active = False
    await db.commit()
    return {"deactivated": True}
