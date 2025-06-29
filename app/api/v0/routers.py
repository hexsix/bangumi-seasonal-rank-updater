from .available_seasons import endpoints as available_seasons_endpoints
from .health import router as health_router

routers = [
    available_seasons_endpoints.router,
    health_router,
]
