from __future__ import annotations

from sqlalchemy.orm.session import Session

"""
Twitscan library
"""
__version__ = "0.0.2"
__author__ = "monkeyusage"
__license__ = "MIT"
import os
from atexit import register
from typing import Any, Callable

import tweepy
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import sessionmaker

consumer_key = os.environ["TWITTER_CONSUMER_KEY"]
consumer_secret = os.environ["TWITTER_CONSUMER_SECRET"]
access_token = os.environ["TWITTER_ACCESS_TOKEN"]
access_token_secret = os.environ["TWITTER_ACCESS_TOKEN_SECRET"]

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)


def config_db(test: bool = False) -> tuple[Engine, Session]:
    engine: Engine = (
        create_engine("sqlite://")
        if test
        else create_engine("sqlite:///data/twitter.db")
    )  # test db is in memory
    _Session: Any = sessionmaker()
    _Session.configure(bind=engine)
    session: Session = _Session()
    return engine, session


engine, session = config_db()
test_engine, test_session = config_db(test=True)

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

register(session.close)
