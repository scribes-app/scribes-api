from .scribes.router import router as scribes_router
from .scribes.db import SCRIBESClient

ROUTERS = [scribes_router]


class APISQLClient(SCRIBESClient):
    """Create MixIn of all databases.
    """


