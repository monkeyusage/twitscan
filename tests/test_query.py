import os
from twitscan import query
from collections.abc import Iterator
from string import hexdigits
from random import choice

TEST_USERNAME = os.environ["TWITSCAN_TEST_USER"]
TEST_USER = query.user_by_screen_name(TEST_USERNAME)
if TEST_USER is None:
    raise Exception("Could not retrieve test user from database")


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
