from .health import router as health_router
from .season import endpoints as season_endpoints
from .update import endpoints as update_endpoints

routers = [
    season_endpoints.router,
    update_endpoints.router,
    health_router,
]
