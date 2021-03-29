from __future__ import annotations
from twitscan.query import user_by_screen_name
from typing import Awaitable
import os

async def get_test_user() -> Awaitable[tuple | None]:
    test_user_name = os.environ['TWITSCAN_TEST_USER']
    test_user = await user_by_screen_name(test_user_name)
    return test_user
