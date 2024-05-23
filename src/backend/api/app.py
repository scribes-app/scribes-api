"""Define app.
"""
import contextlib
import typing as t
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic_settings import BaseSettings
from broadcaster import Broadcast


from ..contexts import ROUTERS, APISQLClient, scribes_router





class OIDCSettings(BaseSettings):
    enabled: bool = False
    issuer_url: str = "http://localhost:8024"
    realm: str = "scribes"
    client_id: str = "scribes-api"
    retry: bool = True
    max_attempts: int = 5


class AppSettings(BaseSettings):
    oidc: OIDCSettings = OIDCSettings()
    database_uri: str = "mysql://root:root@localhost:3306"
    database_name: str = "QD"
    file_storage_path: str = "/Users/sophrobhayek/Documents/dev/scribes-api/uploads/" #TODO: make this relative


def create_app(settings: t.Optional[AppSettings] = None) -> FastAPI:
    """This is the application factory, e.g., a function responsible for
    creating a fresh new instance of application.
    """
    # Parse application settings
    settings = settings or AppSettings()

    # If SCRIBES only mode is set, set scribes to True
    settings.database_name = "scribes"
    settings.database_uri = "postgresql://root:root@localhost:5432"
    broadcast = Broadcast("postgres://root:root@localhost:5432/scribes")

    # check if file storage path exists, else creates it
    if not os.path.exists(settings.file_storage_path):
        os.makedirs(settings.file_storage_path)
        

    # Create database client according to application settings
    db = APISQLClient(
        settings.database_uri, settings.database_name
    )


    # Define application lifespan
    @contextlib.asynccontextmanager
    async def lifespan(app: FastAPI):
        await db.connect()
        await broadcast.connect()
        yield

    # Create fastapi instance
    app = FastAPI(lifespan=lifespan)

    # Attach settings to application
    app.state.settings = settings

    # Attach database to app state
    app.state.database = db

    app.mount("/static", StaticFiles(directory=settings.file_storage_path), name="static")

    # Update Middleware
    app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Attach broadcast to app state
    app.state.broadcast = broadcast


    # Set up the keycloak OIDC client
    from .oidc.provider import oidc_provider
    oidc_provider(app)

    # If scribes only mode is activated, only make
    # available scribes related endpoints
    app.include_router(scribes_router)


    # Return new application instance
    return app

