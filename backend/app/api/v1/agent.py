from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import uuid

from app.core.database import get_db
from app.models.agentic import (
    Workflow,
    RevenueEvent,
    AffiliateLink,
    BudgetConfig,
    AgentTask,
)
from app.models.account import Account, AccountStatus
from app.models.channel import Channel

router = APIRouter(prefix="/agent", tags=["agent"])


# ─── WORKFLOWS ───────────────────────────────────────────────

WORKFLOW_TEMPLATES = {
    "full_pipeline": {
        "name": "Full Growth Pipeline",
        "description": "Import accounts → Assign proxies → Warm → Parse channels → Comment → React",
        "steps": [
            {
                "step": 1,
                "action": "import_accounts",
                "params": {"format": "tdata"},
                "status": "pending",
            },
            {"step": 2, "action": "assign_proxies", "params": {}, "status": "pending"},
            {
                "step": 3,
                "action": "start_warming",
                "params": {"profile": "default"},
                "status": "pending",
            },
            {
                "step": 4,
                "action": "parse_channels",
                "params": {"auto_add": True},
                "status": "pending",
            },
            {
                "step": 5,
                "action": "start_commenting",
                "params": {"workers": 10},
                "status": "pending",
            },
            {
                "step": 6,
                "action": "start_reactions",
                "params": {"workers": 5},
                "status": "pending",
            },
            {
                "step": 7,
                "action": "monitor_bans",
                "params": {"check_interval": 300},
                "status": "pending",
            },
        ],
    },
    "quick_boost": {
        "name": "Quick Channel Boost",
        "description": "Use existing warmed accounts to boost a specific channel",
        "steps": [
            {
                "step": 1,
                "action": "select_warm_accounts",
                "params": {"min_stage": 80},
                "status": "pending",
            },
            {
                "step": 2,
                "action": "subscribe_to_channel",
                "params": {},
                "status": "pending",
            },
            {
                "step": 3,
                "action": "comment_on_posts",
                "params": {"count": 50},
                "status": "pending",
            },
            {
                "step": 4,
                "action": "react_to_comments",
                "params": {"count": 200},
                "status": "pending",
            },
        ],
    },
    "account_recovery": {
        "name": "Account Recovery",
        "description": "Recover and re-warm banned/muted accounts",
        "steps": [
            {
                "step": 1,
                "action": "scan_banned_accounts",
                "params": {},
                "status": "pending",
            },
            {
                "step": 2,
                "action": "rest_period",
                "params": {"hours": 48},
                "status": "pending",
            },
            {
                "step": 3,
                "action": "re_warm",
                "params": {"start_stage": 0},
                "status": "pending",
            },
            {
                "step": 4,
                "action": "validate_recovery",
                "params": {},
                "status": "pending",
            },
        ],
    },
    "revenue_generation": {
        "name": "Revenue Generation",
        "description": "Post affiliate links in target channels, track clicks and conversions",
        "steps": [
            {
                "step": 1,
                "action": "select_affiliate_links",
                "params": {},
                "status": "pending",
            },
            {
                "step": 2,
                "action": "select_warm_accounts",
                "params": {"min_stage": 90},
                "status": "pending",
            },
            {
                "step": 3,
                "action": "post_affiliate_comments",
                "params": {"max_per_channel": 3},
                "status": "pending",
            },
            {
                "step": 4,
                "action": "track_conversions",
                "params": {"period_hours": 72},
                "status": "pending",
            },
            {"step": 5, "action": "report_revenue", "params": {}, "status": "pending"},
        ],
    },
}


@router.get("/workflows/templates")
async def list_templates():
    return [
        {
            "id": k,
            "name": v["name"],
            "description": v["description"],
            "steps": len(v["steps"]),
        }
        for k, v in WORKFLOW_TEMPLATES.items()
    ]


@router.post("/workflows/create")
async def create_workflow(
    template_id: str,
    name: str = "",
    config: str = "{}",
    db: AsyncSession = Depends(get_db),
):
    if template_id not in WORKFLOW_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")

    import json

    tpl = WORKFLOW_TEMPLATES[template_id]
    wf = Workflow(
        id=str(uuid.uuid4()),
        name=name or tpl["name"],
        description=tpl["description"],
        status="idle",
        steps=tpl["steps"],
        config=json.loads(config) if config != "{}" else {},
    )
    db.add(wf)
    await db.commit()
    await db.refresh(wf)
    return {"id": wf.id, "name": wf.name, "steps": len(wf.steps), "status": wf.status}


@router.get("/workflows")
async def list_workflows(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Workflow).order_by(Workflow.created_at.desc()).limit(50)
    )
    return [
        {
            "id": w.id,
            "name": w.name,
            "status": w.status,
            "current_step": w.current_step,
            "total_steps": len(w.steps),
            "stats": w.stats,
            "created_at": w.created_at.isoformat(),
        }
        for w in result.scalars().all()
    ]


@router.post("/workflows/{workflow_id}/start")
async def start_workflow(workflow_id: str, db: AsyncSession = Depends(get_db)):
    wf = await db.get(Workflow, workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    wf.status = "running"
    wf.started_at = datetime.utcnow()
    wf.current_step = 1
    await db.commit()
    return {"started": True, "workflow_id": workflow_id}


@router.post("/workflows/{workflow_id}/pause")
async def pause_workflow(workflow_id: str, db: AsyncSession = Depends(get_db)):
    wf = await db.get(Workflow, workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    wf.status = "paused"
    await db.commit()
    return {"paused": True}


# ─── BULK OPERATIONS ─────────────────────────────────────────


@router.post("/bulk/import-accounts")
async def bulk_import_accounts(
    phones: str = Query(..., description="Comma-separated phone numbers"),
    country_code: str = "+1",
    db: AsyncSession = Depends(get_db),
):
    """Bulk import accounts for agent use."""
    from app.services.account_service import AccountService

    phone_list = [p.strip() for p in phones.split(",") if p.strip()]
    created = []
    for phone in phone_list:
        try:
            acc = await AccountService.create(
                db, phone=phone, country_code=country_code
            )
            created.append(
                {
                    "id": acc.id,
                    "phone": acc.phone,
                    "persona": acc.persona.get("personality_type")
                    if acc.persona
                    else None,
                }
            )
        except Exception as e:
            created.append({"phone": phone, "error": str(e)})

    return {
        "total": len(phone_list),
        "created": len([c for c in created if "error" not in c]),
        "accounts": created,
    }


@router.post("/bulk/assign-proxies")
async def bulk_assign_proxies(db: AsyncSession = Depends(get_db)):
    """Auto-assign proxies to all accounts that need one."""
    from app.services.proxy_service import ProxyService

    result = await db.execute(select(Account).where(Account.proxy_id == None))
    unassigned = list(result.scalars().all())

    assigned = 0
    for acc in unassigned:
        proxy = await ProxyService.assign_to_account(db, acc.id)
        if proxy:
            assigned += 1

    return {"total_unassigned": len(unassigned), "assigned": assigned}


@router.post("/bulk/warm-all")
async def bulk_warm_all(
    profile_id: str = "default",
    db: AsyncSession = Depends(get_db),
):
    """Start warming all eligible accounts."""
    from app.services.warming_service import WarmingService

    result = await db.execute(
        select(Account).where(Account.status == AccountStatus.ACTIVE)
    )
    accounts = list(result.scalars().all())
    ids = [a.id for a in accounts]

    await WarmingService.start_warming(db, ids)
    return {"started_warming": len(ids)}


@router.post("/bulk/subscribe-all")
async def bulk_subscribe_all(
    channel: str = Query(..., description="Channel username"),
    min_warming_stage: int = 60,
    db: AsyncSession = Depends(get_db),
):
    """Subscribe all warm accounts to a channel."""
    from app.telegram.account_actions import AccountActions

    result = await db.execute(
        select(Account).where(
            Account.status.in_([AccountStatus.ACTIVE, AccountStatus.WORKING]),
            Account.warming_stage >= min_warming_stage,
        )
    )
    accounts = list(result.scalars().all())

    success = 0
    for acc in accounts:
        ok = await AccountActions.subscribe_to_channel(db, acc, channel)
        if ok:
            success += 1

    return {"total": len(accounts), "subscribed": success, "channel": channel}


# ─── REVENUE & AFFILIATES ────────────────────────────────────


@router.post("/revenue/add-link")
async def add_affiliate_link(
    name: str,
    url: str,
    campaign: str = "",
    db: AsyncSession = Depends(get_db),
):
    link = AffiliateLink(
        id=str(uuid.uuid4()),
        name=name,
        url=url,
        campaign=campaign or "default",
    )
    db.add(link)
    await db.commit()
    return {"id": link.id, "name": link.name, "url": link.url}


@router.get("/revenue/links")
async def list_affiliate_links(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AffiliateLink).where(AffiliateLink.is_active == True)
    )
    return [
        {
            "id": l.id,
            "name": l.name,
            "url": l.url,
            "campaign": l.campaign,
            "clicks": l.clicks,
            "conversions": l.conversions,
            "revenue": l.revenue,
        }
        for l in result.scalars().all()
    ]


@router.post("/revenue/track-click")
async def track_click(
    link_id: str,
    channel: str = "",
    db: AsyncSession = Depends(get_db),
):
    link = await db.get(AffiliateLink, link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    link.clicks += 1
    event = RevenueEvent(
        id=str(uuid.uuid4()),
        event_type="click",
        source=channel,
        affiliate_link_id=link_id,
        affiliate_link=link.url,
        channel=channel,
    )
    db.add(event)
    await db.commit()
    return {"tracked": True, "total_clicks": link.clicks}


@router.post("/revenue/track-conversion")
async def track_conversion(
    link_id: str,
    amount: float = 0.0,
    currency: str = "USD",
    db: AsyncSession = Depends(get_db),
):
    link = await db.get(AffiliateLink, link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    link.conversions += 1
    link.revenue += amount
    event = RevenueEvent(
        id=str(uuid.uuid4()),
        event_type="conversion",
        source="affiliate",
        affiliate_link_id=link_id,
        affiliate_link=link.url,
        amount=amount,
        currency=currency,
    )
    db.add(event)
    await db.commit()
    return {"tracked": True, "total_revenue": link.revenue}


@router.get("/revenue/summary")
async def revenue_summary(db: AsyncSession = Depends(get_db)):
    total_links = (await db.execute(select(func.count(AffiliateLink.id)))).scalar()
    total_clicks = (
        await db.execute(select(func.sum(AffiliateLink.clicks)))
    ).scalar() or 0
    total_conversions = (
        await db.execute(select(func.sum(AffiliateLink.conversions)))
    ).scalar() or 0
    total_revenue = (
        await db.execute(select(func.sum(AffiliateLink.revenue)))
    ).scalar() or 0

    today = datetime.utcnow().replace(hour=0, minute=0, second=0)
    today_events = (
        await db.execute(
            select(func.count(RevenueEvent.id)).where(RevenueEvent.timestamp >= today)
        )
    ).scalar()

    return {
        "total_links": total_links,
        "total_clicks": total_clicks,
        "total_conversions": total_conversions,
        "total_revenue": round(total_revenue, 2),
        "conversion_rate": round((total_conversions / max(total_clicks, 1)) * 100, 2),
        "events_today": today_events,
    }


# ─── BUDGET ──────────────────────────────────────────────────


@router.get("/budget/status")
async def budget_status(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BudgetConfig))
    budgets = list(result.scalars().all())
    if not budgets:
        defaults = ["proxies", "accounts", "ai", "total"]
        for cat in defaults:
            b = BudgetConfig(id=str(uuid.uuid4()), category=cat)
            db.add(b)
        await db.commit()
        result = await db.execute(select(BudgetConfig))
        budgets = list(result.scalars().all())

    return [
        {
            "category": b.category,
            "daily_limit": b.daily_limit,
            "monthly_limit": b.monthly_limit,
            "daily_spent": b.daily_spent,
            "monthly_spent": b.monthly_spent,
            "daily_remaining": round(b.daily_limit - b.daily_spent, 2),
            "monthly_remaining": round(b.monthly_limit - b.monthly_spent, 2),
            "alert_at_pct": b.alert_at_pct,
            "auto_stop": b.auto_stop_at_limit,
        }
        for b in budgets
    ]


@router.put("/budget/update")
async def update_budget(
    category: str,
    daily_limit: float = 0,
    monthly_limit: float = 0,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BudgetConfig).where(BudgetConfig.category == category)
    )
    budget = result.scalar_one_or_none()
    if not budget:
        budget = BudgetConfig(id=str(uuid.uuid4()), category=category)
        db.add(budget)
    if daily_limit > 0:
        budget.daily_limit = daily_limit
    if monthly_limit > 0:
        budget.monthly_limit = monthly_limit
    budget.updated_at = datetime.utcnow()
    await db.commit()
    return {"updated": True, "category": category}


# ─── TASK QUEUE (for agent scheduling) ───────────────────────


@router.post("/tasks/enqueue")
async def enqueue_task(
    task_type: str,
    priority: int = 5,
    params: str = "{}",
    db: AsyncSession = Depends(get_db),
):
    """Enqueue a task for autonomous agent processing."""
    import json

    task = AgentTask(
        id=str(uuid.uuid4()),
        task_type=task_type,
        priority=priority,
        params=json.loads(params) if params != "{}" else {},
    )
    db.add(task)
    await db.commit()
    return {"task_id": task.id, "type": task_type, "priority": priority}


@router.get("/tasks/pending")
async def get_pending_tasks(limit: int = 10, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AgentTask)
        .where(AgentTask.status == "pending")
        .order_by(AgentTask.priority.asc(), AgentTask.created_at.asc())
        .limit(limit)
    )
    return [
        {
            "id": t.id,
            "type": t.task_type,
            "priority": t.priority,
            "params": t.params,
            "created_at": t.created_at.isoformat(),
        }
        for t in result.scalars().all()
    ]


@router.get("/status")
async def agent_status(db: AsyncSession = Depends(get_db)):
    """Full status report for agent decision making."""
    total = (await db.execute(select(func.count(Account.id)))).scalar()
    active = (
        await db.execute(
            select(func.count(Account.id)).where(
                Account.status.in_(["active", "working"])
            )
        )
    ).scalar()
    warming = (
        await db.execute(
            select(func.count(Account.id)).where(Account.status == "warming")
        )
    ).scalar()
    banned = (
        await db.execute(
            select(func.count(Account.id)).where(Account.status == "banned")
        )
    ).scalar()
    channels = (await db.execute(select(func.count(Channel.id)))).scalar()
    target_channels = (
        await db.execute(
            select(func.count(Channel.id)).where(Channel.is_target == True)
        )
    ).scalar()
    pending_tasks = (
        await db.execute(
            select(func.count(AgentTask.id)).where(AgentTask.status == "pending")
        )
    ).scalar()
    running_workflows = (
        await db.execute(
            select(func.count(Workflow.id)).where(Workflow.status == "running")
        )
    ).scalar()

    return {
        "accounts": {
            "total": total,
            "active": active,
            "warming": warming,
            "banned": banned,
        },
        "channels": {"total": channels, "targets": target_channels},
        "tasks": {"pending": pending_tasks},
        "workflows": {"running": running_workflows},
        "can_comment": active > 0 and target_channels > 0,
        "can_react": active > 0 and target_channels > 0,
        "needs_warming": active > 0 and (active + warming) == total,
    }
