from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import PromptTemplate


router = APIRouter(prefix="/prompts", tags=["prompts"])


BUILT_IN_PROMPTS = [
    {
        "name": "Hater",
        "tone": "Critical, dismissive, arrogant",
        "use_case": "Provokes clicks from curious readers",
        "system_prompt": "You are a skeptical Telegram user. Write a short critical or dismissive comment. Be blunt. 15-30 words.",
        "temperature": 0.8,
        "max_tokens": 50,
    },
    {
        "name": "Expert",
        "tone": "Knowledgeable, helpful",
        "use_case": "Crypto, finance, education",
        "system_prompt": "You are an expert in this topic. Add a helpful insight. 15-35 words.",
        "temperature": 0.6,
        "max_tokens": 60,
    },
    {
        "name": "Question",
        "tone": "Curious, engaging",
        "use_case": "Increases comment thread activity",
        "system_prompt": "You are a curious person. Ask an interesting question. 10-25 words.",
        "temperature": 0.75,
        "max_tokens": 40,
    },
    {
        "name": "Controversial",
        "tone": "Polarizing opinion",
        "use_case": "Drives debate and profile clicks",
        "system_prompt": "You have a strong, controversial opinion. State it boldly. 15-30 words.",
        "temperature": 0.85,
        "max_tokens": 50,
    },
    {
        "name": "Supportive",
        "tone": "Agreeable, encouraging",
        "use_case": "Builds positive presence",
        "system_prompt": "You strongly agree with this post. Write a supportive comment. 10-25 words.",
        "temperature": 0.7,
        "max_tokens": 40,
    },
]


@router.get("")
async def list_prompts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PromptTemplate).where(PromptTemplate.is_active == True)
    )
    prompts = list(result.scalars().all())
    if not prompts:
        return BUILT_IN_PROMPTS
    return [
        {
            "id": p.id,
            "name": p.name,
            "tone": p.tone,
            "use_case": p.use_case,
            "system_prompt": p.system_prompt,
            "temperature": p.temperature,
            "max_tokens": p.max_tokens,
            "is_active": p.is_active,
            "version": p.version,
        }
        for p in prompts
    ]


@router.post("")
async def create_prompt(
    name: str,
    tone: str,
    use_case: str,
    system_prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 100,
    db: AsyncSession = Depends(get_db),
):
    import uuid

    prompt = PromptTemplate(
        id=str(uuid.uuid4()),
        name=name,
        tone=tone,
        use_case=use_case,
        system_prompt=system_prompt,
        user_prompt_template="Post: {post_text}\nWrite a comment:",
        temperature=temperature,
        max_tokens=max_tokens,
    )
    db.add(prompt)
    await db.commit()
    return {"id": prompt.id, "name": prompt.name}


@router.delete("/{prompt_id}")
async def delete_prompt(prompt_id: str, db: AsyncSession = Depends(get_db)):
    prompt = await db.get(PromptTemplate, prompt_id)
    if prompt:
        prompt.is_active = False
        await db.commit()
        return {"deactivated": True}
    raise HTTPException(status_code=404, detail="Prompt not found")
