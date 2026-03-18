from fastapi import APIRouter
from app.api.v1 import (
    accounts,
    account_profile,
    proxies,
    channels,
    commenting,
    warming,
    warming_config,
    reactions,
    analytics,
    prompts,
    agent,
    behaviors,
    parsers,
    llm_config,
    troubleshoot,
    killswitch,
    scalability,
)

api_router = APIRouter()

api_router.include_router(accounts.router)
api_router.include_router(account_profile.router)
api_router.include_router(proxies.router)
api_router.include_router(channels.router)
api_router.include_router(commenting.router)
api_router.include_router(warming.router)
api_router.include_router(warming_config.router)
api_router.include_router(reactions.router)
api_router.include_router(analytics.router)
api_router.include_router(prompts.router)
api_router.include_router(agent.router)
api_router.include_router(behaviors.router)
api_router.include_router(parsers.router)
api_router.include_router(llm_config.router)
api_router.include_router(troubleshoot.router)
api_router.include_router(killswitch.router)
api_router.include_router(scalability.router)


@api_router.get("/status")
async def status():
    return {"status": "running"}
