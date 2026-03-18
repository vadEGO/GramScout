from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import uuid
import os
import glob as globmod

from app.core.database import get_db
from app.core.logging import logger
from app.models.llm_config import TroubleshootSession, LLMProvider

router = APIRouter(tags=["troubleshoot"])


DIAGNOSTIC_PROMPT = """You are an expert Telegram automation engineer and Python developer.
Analyze the following system information and error logs to diagnose issues and suggest fixes.

SYSTEM INFO:
{system_info}

RECENT LOGS:
{logs}

CURRENT CONFIG:
{config}

USER QUERY:
{query}

Provide a diagnosis and actionable fixes in this JSON format:
{{
  "severity": "info|warning|error|critical",
  "summary": "One-line summary of the issue",
  "diagnosis": "Detailed explanation of what's wrong",
  "root_cause": "Why this is happening",
  "fixes": [
    {{
      "action": "description of what to do",
      "config_change": "exact config change if applicable",
      "command": "shell command if applicable",
      "confidence": 0.0-1.0
    }}
  ],
  "prevention": "How to prevent this in the future"
}}"""


def _collect_system_info() -> dict:
    """Collect system diagnostic information."""
    import platform
    import subprocess

    info = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "hostname": platform.node(),
    }

    # Docker status
    try:
        result = subprocess.run(
            ["docker", "compose", "ps", "--format", "json"],
            capture_output=True,
            text=True,
            cwd="/Users/vaddylandbot/GramScout",
            timeout=10,
        )
        info["docker_services"] = "running" if result.returncode == 0 else "error"
    except:
        info["docker_services"] = "unknown"

    # Disk space
    try:
        result = subprocess.run(
            ["df", "-h", "/"], capture_output=True, text=True, timeout=5
        )
        info["disk"] = (
            result.stdout.strip().split("\n")[-1]
            if result.returncode == 0
            else "unknown"
        )
    except:
        info["disk"] = "unknown"

    # Memory
    try:
        result = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=5)
        info["memory"] = result.stdout[:200] if result.returncode == 0 else "unknown"
    except:
        info["memory"] = "unknown"

    return info


def _collect_logs(
    log_dir: str = "/Users/vaddylandbot/GramScout/backend/logs", max_lines: int = 200
) -> str:
    """Collect recent log entries."""
    if not os.path.exists(log_dir):
        return "No log files found. Application logs are streamed to Docker stdout."

    log_files = globmod.glob(os.path.join(log_dir, "*.log"))
    if not log_files:
        return "No log files found."

    all_logs = []
    for f in sorted(log_files)[-3:]:  # Last 3 log files
        try:
            with open(f) as fh:
                lines = fh.readlines()[-max_lines:]
                all_logs.extend(lines)
        except:
            pass

    return "".join(all_logs[-max_lines:]) if all_logs else "No log entries."


def _collect_config() -> dict:
    """Collect current configuration (sanitized)."""
    try:
        from app.config import settings

        return {
            "database_url": settings.DATABASE_URL.split("@")[-1]
            if "@" in settings.DATABASE_URL
            else "not set",
            "redis_url": settings.REDIS_URL.split("@")[-1]
            if "@" in settings.REDIS_URL
            else "not set",
            "debug": settings.DEBUG,
            "max_concurrent_workers": settings.MAX_CONCURRENT_WORKERS,
            "comment_delay_min": settings.DEFAULT_COMMENT_DELAY_MIN,
            "comment_delay_max": settings.DEFAULT_COMMENT_DELAY_MAX,
            "telegram_api_id": "set" if settings.TELEGRAM_API_ID else "NOT SET",
            "telegram_api_hash": "set" if settings.TELEGRAM_API_HASH else "NOT SET",
            "openrouter_api_key": "set" if settings.OPENROUTER_API_KEY else "NOT SET",
        }
    except Exception as e:
        return {"error": f"Could not load config: {e}"}


def _collect_docker_logs(service: str = "backend", lines: int = 50) -> str:
    """Collect Docker container logs."""
    import subprocess

    try:
        result = subprocess.run(
            ["docker", "compose", "logs", service, "--tail", str(lines)],
            capture_output=True,
            text=True,
            cwd="/Users/vaddylandbot/GramScout",
            timeout=10,
        )
        return result.stdout[-3000:] if result.stdout else f"No logs for {service}"
    except Exception as e:
        return f"Could not collect docker logs: {e}"


# ─── ENDPOINTS ────────────────────────────────────────────────


@router.get("/troubleshoot/status")
async def system_status():
    """Quick system health overview."""
    info = _collect_system_info()

    import subprocess

    # Check each service
    services = {}
    for svc in ["backend", "frontend", "postgres", "redis"]:
        try:
            result = subprocess.run(
                ["docker", "compose", "ps", svc, "--format", "{{.Status}}"],
                capture_output=True,
                text=True,
                cwd="/Users/vaddylandbot/GramScout",
                timeout=5,
            )
            services[svc] = result.stdout.strip() or "not running"
        except:
            services[svc] = "unknown"

    config = _collect_config()

    return {
        "system": info,
        "services": services,
        "config": config,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/troubleshoot/logs/{service}")
async def get_service_logs(service: str = "backend", lines: int = 100):
    """Get logs for a specific service."""
    logs = _collect_docker_logs(service, lines)
    return {"service": service, "logs": logs}


@router.post("/troubleshoot/analyze")
async def analyze_system(
    query: str = "Analyze the system and identify any issues",
    include_logs: bool = True,
    include_config: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """Run LLM-powered system analysis."""

    # Collect data
    system_info = _collect_system_info()
    logs = (
        _collect_docker_logs("backend", 200) if include_logs else "Logs not requested"
    )
    config = _collect_config() if include_config else {}

    # Build prompt
    prompt = DIAGNOSTIC_PROMPT.format(
        system_info=str(system_info),
        logs=logs[-3000:],  # Limit log size
        config=str(config),
        query=query,
    )

    # Create session record
    session = TroubleshootSession(
        id=str(uuid.uuid4()),
        user_query=query,
        status="analyzing",
    )
    db.add(session)
    await db.commit()

    # Try to use LLM for analysis
    try:
        from app.ai.llm_client import OpenRouterClient

        client = OpenRouterClient()

        if not client.api_key:
            session.status = "completed"
            session.diagnosis = "No OpenRouter API key configured. Add one in Settings > LLM Configuration to enable AI troubleshooting."
            session.fixes_applied = {
                "manual_steps": [
                    "Go to Settings > LLM Configuration",
                    "Add your OpenRouter API key (sk-or-...)",
                    "Save and test the connection",
                    "Run troubleshoot again",
                ]
            }
            await db.commit()
            return {
                "session_id": session.id,
                "status": "needs_api_key",
                "message": session.diagnosis,
                "manual_steps": session.fixes_applied["manual_steps"],
            }

        result = await client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model="openai/gpt-4o-mini",
            temperature=0.2,
            max_tokens=1500,
        )
        await client.close()

        session.status = "completed"
        session.diagnosis = result or "No diagnosis returned"
        session.completed_at = datetime.utcnow()
        await db.commit()

        return {
            "session_id": session.id,
            "status": "completed",
            "diagnosis": result,
            "system_info": system_info,
            "config_status": config,
        }

    except Exception as e:
        session.status = "failed"
        session.diagnosis = f"Analysis failed: {str(e)}"
        session.completed_at = datetime.utcnow()
        await db.commit()

        return {
            "session_id": session.id,
            "status": "failed",
            "error": str(e),
            "system_info": system_info,
            "config_status": config,
        }


@router.get("/troubleshoot/sessions")
async def list_sessions(limit: int = 20, db: AsyncSession = Depends(get_db)):
    """List past troubleshooting sessions."""
    result = await db.execute(
        select(TroubleshootSession)
        .order_by(TroubleshootSession.created_at.desc())
        .limit(limit)
    )
    return [
        {
            "id": s.id,
            "query": s.user_query,
            "status": s.status,
            "diagnosis_preview": (s.diagnosis or "")[:100],
            "created_at": s.created_at.isoformat(),
        }
        for s in result.scalars().all()
    ]


@router.post("/troubleshoot/fix-config")
async def apply_config_fix(
    key: str,
    value: str,
):
    """Apply a configuration fix suggested by troubleshooter."""
    config_file = "/Users/vaddylandbot/GramScout/.env"

    try:
        if os.path.exists(config_file):
            with open(config_file) as f:
                lines = f.readlines()

            updated = False
            for i, line in enumerate(lines):
                if line.strip().startswith(f"{key}="):
                    lines[i] = f"{key}={value}\n"
                    updated = True
                    break

            if not updated:
                lines.append(f"{key}={value}\n")

            with open(config_file, "w") as f:
                f.writelines(lines)

            return {
                "applied": True,
                "key": key,
                "message": "Run 'make restart' to apply changes",
            }
        else:
            return {"applied": False, "error": ".env file not found"}

    except Exception as e:
        return {"applied": False, "error": str(e)}


@router.post("/troubleshoot/quick-check")
async def quick_check():
    """Quick automated checks without LLM (always available)."""
    issues = []
    warnings = []

    config = _collect_config()

    # Check required config
    if config.get("telegram_api_id") == "NOT SET":
        issues.append(
            "TELEGRAM_API_ID not configured — add in Settings > LLM Configuration"
        )
    if config.get("telegram_api_hash") == "NOT SET":
        issues.append("TELEGRAM_API_HASH not configured")
    if config.get("openrouter_api_key") == "NOT SET":
        warnings.append("OPENROUTER_API_KEY not configured — AI features won't work")

    # Check services
    import subprocess

    for svc in ["backend", "postgres", "redis"]:
        try:
            result = subprocess.run(
                ["docker", "compose", "ps", svc, "--format", "{{.Status}}"],
                capture_output=True,
                text=True,
                cwd="/Users/vaddylandbot/GramScout",
                timeout=5,
            )
            if "healthy" not in result.stdout and "Up" not in result.stdout:
                issues.append(f"Service {svc} is not healthy")
        except:
            issues.append(f"Could not check service {svc}")

    return {
        "issues": issues,
        "warnings": warnings,
        "healthy": len(issues) == 0,
        "config": config,
    }
