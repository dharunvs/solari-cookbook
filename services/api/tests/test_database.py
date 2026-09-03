import asyncio

import pytest
from noxyn_api.database import database_is_ready


@pytest.mark.integration
def test_postgresql_accepts_connections() -> None:
    assert asyncio.run(database_is_ready())
