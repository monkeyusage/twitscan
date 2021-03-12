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
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.asyncio.engine import AsyncEngine
from sqlalchemy.orm import sessionmaker

from twitscan.models import (
    Entourage,
    Hashtag,
    Interaction,
    Link,
    Mention,
    TwitscanStatus,
    TwitscanUser,
)

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


engine, session = config_db()
test_engine, test_session = config_db(test=True)

config: dict[str, int] = {
    "MAX_FOLLOWERS": 200,
    "MAX_TWEETS": 200,
}


def db_info() -> dict[str, int]:
    info = {
        "user": len(session.query(TwitscanUser).all()),
        "entourage": len(session.query(Entourage).all()),
        "interaction": len(session.query(Interaction).all()),
        "status": len(session.query(TwitscanStatus).all()),
        "mention": len(session.query(Mention).all()),
        "urls": len(session.query(Link).all()),
        "hashtags": len(session.query(Hashtag).all()),
    }
    return info


assert (
    config["MAX_TWEETS"] <= 200
), "Twitter API accepts retrieval of maximum 3200 tweets for each user"

api = tweepy.API(
    auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True
)
