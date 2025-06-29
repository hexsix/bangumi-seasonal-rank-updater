from .health import router as health_router
from .season import endpoints as season_endpoints
from .subject import router as subject_router
from .update import endpoints as update_endpoints

routers = [
    health_router,
    season_endpoints.router,
    subject_router,
    update_endpoints.router,
]
