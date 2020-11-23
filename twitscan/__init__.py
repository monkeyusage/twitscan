from typing import Any, Tuple
import tweepy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .secret import auth


def config_db(test: bool = False) -> Tuple[Any, Any]:
    if test:
        engine = create_engine("sqlite://")  # in memory db
    else:
        engine = create_engine("sqlite:///data/twitter.db")
    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()
    return engine, session


engine, session = config_db()
test_engine, test_session = config_db(test=True)

api = tweepy.API(
    auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True
)
