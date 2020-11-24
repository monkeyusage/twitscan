from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from typing import Any

Base: Any = declarative_base()

if __name__ == "__main__":
    from sqlalchemy import create_engine

    engine = create_engine("sqlite:///data/twitter.db")
    Base.metadata.bind = engine


class Status(Base):
    __tablename__ = "status"
    status_id = Column(Integer, primary_key=True)
    text = Column(String)
    created_at = Column(Date, nullable=False)
    favorite_count = Column(Integer, nullable=False)
    retweet_count = Column(Integer, nullable=False)
    in_reply_to_status_id = Column(Integer)
    in_reply_to_user_id = Column(Integer)
    is_retweet = Column(Boolean, nullable=False)
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False)
    user_mentions = relationship("Mention", backref=backref("status"), lazy=True)


class Mention(Base):
    __tablename__ = "mention"
    mention_id = Column(Integer, primary_key=True)
    status_id = Column(Integer, ForeignKey("status.status_id"), nullable=False)
    user_id = Column(Integer, nullable=False)  # might not be analysed user


class User(Base):
    __tablename__ = "user"
    user_id = Column(Integer, primary_key=True)
    screen_name = Column(String, nullable=False)
    created_at = Column(Date, nullable=False)
    verified = Column(Boolean, nullable=False)
    favorites_count = Column(Integer, nullable=False)
    status_count = Column(Integer, nullable=False, default=0)
    friends_count = Column(Integer, nullable=False, default=0)
    followers_count = Column(Integer, nullable=False, default=0)
    chirps = relationship(
        "Status", backref=backref("user"), lazy=True
    )  # either tweets or retweets
    entourage = relationship("Entourage", backref=backref("user"), lazy=True)
    interacted_tweets = relationship("Interaction", backref=backref("user"), lazy=True)


class Interaction(Base):
    __tablename__ = "interaction"
    interaction_id = Column("interaction_id", Integer, primary_key=True)
    user_id = Column("user_id", Integer, ForeignKey("user.user_id"))
    status_id = Column("status_id", Integer, ForeignKey("status.status_id"))
    like = Column("like", Boolean, nullable=False)
    retweet = Column("retweet", Boolean, nullable=False)
    comment = Column("comment", Boolean, nullable=False)


class Entourage(Base):
    __tablename__ = "friend"
    entourage_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False)
    friend_follower_id = Column(Integer, nullable=False)
    friend = Column(Boolean, nullable=False)  # might not be analysed user
    follower = Column(Boolean, nullable=False)  # might not be analysed user


if __name__ == "__main__":
    Base.metadata.create_all()
