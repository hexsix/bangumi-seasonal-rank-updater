from .health import router as health_router
from .index import router as index_router
from .season import endpoints as season_endpoints
from .subject import router as subject_router
from .update import endpoints as update_endpoints
from .yucwiki import router as yucwiki_router

routers = [
    health_router,
    index_router,
    season_endpoints.router,
    subject_router,
    update_endpoints.router,
    yucwiki_router,
]
