import os
import asyncio
from typing import Coroutine
from twitscan import query
from collections.abc import Iterator
from string import hexdigits
from random import choice


async def fetch_user():
    user_name = os.environ["TWITSCAN_TEST_USER"]
    user = await query.user_by_screen_name(user_name)
    if user is None:
        raise Exception("Could not retrieve test user from database")
    return user_name, user

TEST_USERNAME, TEST_USER = asyncio.get_event_loop().run_until_complete(fetch_user())

def test_user_by_screen_name():
    nonce = "".join([choice(hexdigits) for _ in range(999999)])
    user_name = "SomeNonSensicalUserName" + nonce
    user = query.user_by_screen_name(user_name)
    assert user is None


def test_followers():
    followers = query.followers(TEST_USER)
    assert isinstance(
        followers, Iterator
    ), "return type of followers query should be iterator"
