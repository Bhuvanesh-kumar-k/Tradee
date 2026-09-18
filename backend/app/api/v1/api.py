from fastapi import APIRouter
from app.api.v1 import auth, settings, scanner, trades, telegram, system

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(settings.router)
api_router.include_router(scanner.router)
api_router.include_router(trades.router)
api_router.include_router(telegram.router)
api_router.include_router(system.router)