from __future__ import annotations

"""
Twitscan library
"""
__version__ = "0.0.1"
__author__ = "monkeyusage"
__license__ = "MIT"
import os
import asyncio
from typing import Any

import tweepy
import aiosqlite
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import sessionmaker

consumer_key = os.environ.get("TWITTER_CONSUMER_KEY", None)
consumer_secret = os.environ.get("TWITTER_CONSUMER_SECRET", None)
access_token = os.environ.get("TWITTER_ACCESS_TOKEN", None)
access_token_secret = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET", None)

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)


def config_db(test: bool = False) -> tuple[Engine, Any]:
    if test:
        engine: Engine = create_engine("sqlite://")  # in memory db
    else:
        engine = create_engine("sqlite:///data/twitter.db")
    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()
    return engine, session


async def get_async_session():
    session = await aiosqlite.connect("data/twitter.db")
    return session


engine, sync_session = config_db()
test_engine, test_session = config_db(test=True)
async_session = asyncio.get_event_loop().run_until_complete(get_async_session())

config: dict[str, int] = {
    "MAX_FOLLOWERS": 200,
    "MAX_TWEETS": 200,
}


assert (
    config["MAX_TWEETS"] <= 200
), "Twitter API accepts retrieval of maximum 3200 tweets for each user"

api = tweepy.API(
    auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True
)
