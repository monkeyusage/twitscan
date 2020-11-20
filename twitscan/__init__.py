import tweepy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .secret import auth

engine = create_engine("sqlite:///data/twitter.db")

Session = sessionmaker()
Session.configure(bind=engine)

session = Session()
api = tweepy.API(
    auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True
)
