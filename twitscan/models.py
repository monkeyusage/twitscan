from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean, Table
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

if __name__ == "__main__":
    import sqlalchemy
    engine = sqlalchemy.create_engine("sqlite:///data/twitter.db")
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
    user_mentions = relationship("Mention", backref=backref("status"))

class Mention(Base):
    __tablename__ = "mention"
    mention_id = Column(Integer, primary_key=True)
    status_id = Column(Integer, ForeignKey("status.status_id"), nullable=False)
    user_id = Column(Integer, nullable=False)

interacted_status = Table(
    "interacted_status",
    Base.metadata,
    Column("status_id", Integer, ForeignKey("status.status_id")),
    Column("user_id", Integer, ForeignKey("user.user_id")),
    Column("liked", Boolean, nullable=False),
    Column("retweeted", Boolean, nullable=False)
)

class User(Base):
    __tablename__ = "user"
    user_id = Column(Integer, primary_key=True)
    created_at = Column(Date)
    verified = Column(Boolean, nullable=False)
    favorites_count = Column(Integer, nullable=False)
    status_count = Column(Integer, nullable=False, default=0)
    friends_count = Column(Integer, nullable=False, default=0)
    followers_count = Column(Integer, nullable=False, default=0)
    tweets = relationship("Status", backref=backref("user"))
    friends = relationship("Friend", backref=backref("user"))
    followers = relationship("Follower", backref=backref("user"))
    interacted_tweets = relationship("Status", secondary=interacted_status, back_populates="user")

class Friend(Base):
    __tablename__ = "friend"
    friendship_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False)
    friend_id = Column(Integer, nullable=False)


class Follower(Base):
    __tablename__ = "follower"
    followership_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.user_id"))
    follower_id = Column(Integer, nullable=False)

if __name__ == "__main__":
    Base.metadata.create_all()
    