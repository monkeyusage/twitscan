from __future__ import annotations

import os
from typing import Awaitable

from twitscan.query import session, user_by_screen_name


async def get_test_user() -> Awaitable[tuple | None]:
    test_user_name = os.environ["TWITSCAN_TEST_USER"]
    test_user = await user_by_screen_name(test_user_name)
    return test_user


async def execute(sql: str) -> Awaitable[list[tuple | None]]:
    cursor = await session.execute(sql)
    results = await cursor.fetchall()
    return results
