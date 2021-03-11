from __future__ import annotations
from twitscan import async_session
from sqlalchemy import select
from twitscan.models import (
    Entourage,
    Hashtag,
    Interaction,
    Link,
    Mention,
    TwitscanStatus,
    TwitscanUser,
)


def followers(user: TwitscanUser) -> list[TwitscanUser]:
    maybe_followers: list[TwitscanUser | None] = [
        user_by_id(ent.friend_follower_id) for ent in user.entourage if ent.follower
    ]
    scanned_followers: list[TwitscanUser] = [
        follower for follower in maybe_followers if follower is not None
    ]
    return scanned_followers


def friends(user: TwitscanUser) -> list[TwitscanUser]:
    maybe_friend: list[TwitscanUser | None] = [
        user_by_id(ent.friend_follower_id) for ent in user.entourage if ent.friend
    ]
    scanned_friend: list[TwitscanUser] = [
        friend for friend in maybe_friend if friend is not None
    ]
    return scanned_friend


def entourage(user: TwitscanUser) -> list[int]:
    maybe_entourage: list[TwitscanUser | None] = [
        user_by_id(ent.friend_follower_id) for ent in user.entourage
    ]
    scanned_entourage: list[TwitscanUser] = [
        ent for ent in maybe_entourage if ent is not None
    ]
    return scanned_entourage


def common_followers(user_a: TwitscanUser, user_b: TwitscanUser) -> set[TwitscanUser]:
    followers_a: set[TwitscanUser] = set(followers(user_a))
    followers_b: set[TwitscanUser] = set(followers(user_b))
    return followers_a & followers_b


def common_friends(user_a: TwitscanUser, user_b: TwitscanUser) -> set[TwitscanUser]:
    friends_a: set[TwitscanUser] = set(friends(user_a))
    friends_b: set[TwitscanUser] = set(friends(user_b))
    return friends_a & friends_b


def common_entourage(user_a: TwitscanUser, user_b: TwitscanUser) -> set[TwitscanUser]:
    entourage_a: set[TwitscanUser] = set(entourage(user_a))
    entourage_b: set[TwitscanUser] = set(entourage(user_b))
    return entourage_a & entourage_b


async def all_users() -> list[TwitscanUser]:
    with async_session() as session:
        result = await session.execute(select(TwitscanUser))
    


async def all_statuses() -> list[TwitscanStatus]:
    with async_session() as session:
        result = await session.execute(select(TwitscanStatus))
    return result


async def all_interations() -> list[Interaction]:
    with async_session() as session:
        result = await session.execute(select(Interaction)).all()
    return result

async def all_entourages() -> list[Entourage]:
    with async_session() as session:
        result = await session.execute(select(Entourage)).all()
    return result

async def all_mentions() -> list[Mention]:
    with async_session() as session:
        result = await session.execute(select(Mention)).all()
    return result

async def all_links() -> list[Link]:
    with async_session() as session:
        result = await session.execute(select(Link))
    return result.all()

async def all_hashtags() -> list[Hashtag]:
    with async_session() as session:
        result = await session.execute(select(Hashtag))
    return result.all()

async def user_by_screen_name(screen_name: str) -> TwitscanUser | None:
    """queries user by screen name"""
    with async_session() as session:
        stmt = select(TwitscanUser).where(TwitscanUser.screen_name == screen_name)
        result = await session.execute(stmt)
    return result.first()


async def user_by_id(user_id: int) -> TwitscanUser | None:
    with async_session() as session:
        stmt = select(TwitscanUser).where(TwitscanUser.user_id == user_id)
        result = await session.execute(stmt)
    return result.first()

def hashtags_used(user: TwitscanUser) -> set[Hashtag]:
    """takes user and returns used hashtags"""
    used_ht: set[Hashtag] = set()
    for chirp in user.chirps:
        hashtags = [hashtag.hashtag_name for hashtag in chirp.hashtags]
        used_ht.update(hashtags)
    return used_ht


def common_hashtags(user_a: TwitscanUser, user_b: TwitscanUser) -> set[Hashtag]:
    ht_a: set[Hashtag] = hashtags_used(user_a)
    ht_b: set[Hashtag] = hashtags_used(user_b)
    return ht_a & ht_b


def status_by_id(status_id: int) -> TwitscanStatus | None:
    return (
        session.query(TwitscanStatus)
        .filter(TwitscanStatus.status_id == status_id)
        .first()
    )


def statuses_by_hashtag(hashtag: str) -> list[TwitscanStatus]:
    hashtags = session.query(Hashtag).filter(Hashtag.hashtag_name == hashtag).all()
    statuses = [ht.status for ht in hashtags]
    return statuses


def find_status(string: str) -> list[TwitscanStatus]:
    string = "%" + string + "%"
    return session.query(TwitscanStatus).filter(TwitscanStatus.text.ilike(string)).all()


def find_user(name: str) -> list[TwitscanUser]:
    name = "%" + name + "%"
    return (
        session.query(TwitscanUser).filter(TwitscanUser.screen_name.ilike(name)).all()
    )


def similarity(user_a: TwitscanUser, user_b: TwitscanUser) -> int:
    """computes similarity score between user_a to user_b :=> the higher the more similar"""
    c_friends: set[TwitscanUser] = common_friends(user_a, user_b)
    c_followers: set[TwitscanUser] = common_followers(user_a, user_b)
    c_hash_tags: set[Hashtag] = common_hashtags(user_a, user_b)
    return (len(c_friends) + len(c_followers)) * 2 + len(c_hash_tags)


def interaction(user_a: TwitscanUser, user_b: TwitscanUser) -> int:
    """computes interaction score from user_a to user_b :=> the higher the more interaction"""
    # get all interacted tweets from user_a
    interacted_tweets: list[Interaction] = user_a.interacted_tweets

    # filter by kind of interactions
    all_comments: list[TwitscanStatus | None] = [
        status_by_id(tweet.status_id) for tweet in interacted_tweets if tweet.comment
    ]
    all_retweets: list[TwitscanStatus | None] = [
        status_by_id(tweet.status_id) for tweet in interacted_tweets if tweet.retweet
    ]
    all_likes: list[TwitscanStatus | None] = [
        status_by_id(tweet.status_id) for tweet in interacted_tweets if tweet.like
    ]

    # normally all statuses should be in database but lets not take any risk and filter the lists
    scanned_comments: list[TwitscanStatus] = [
        status for status in all_comments if status is not None
    ]
    scanned_retweets: list[TwitscanStatus] = [
        status for status in all_retweets if status is not None
    ]
    scanned_likes: list[TwitscanStatus] = [
        status for status in all_likes if status is not None
    ]

    # apply filter interaction should be with status made by user_b, apply weight for each category
    comments: list[int] = [
        3 for comment in scanned_comments if comment.user_id == user_b.user_id
    ]
    retweets: list[int] = [
        2 for retweet in scanned_retweets if retweet.user_id == user_b.user_id
    ]
    likes: list[int] = [1 for like in scanned_likes if like.user_id == user_b.user_id]

    return sum([sum(l) for l in (comments, retweets, likes)])


def engagement(user_a: TwitscanUser, user_b: TwitscanUser) -> int:
    """computes the engagement of user_a towards user_b :=> the higher the more engagement"""
    interaction_score: int = interaction(user_a, user_b)
    similarity_score: int = similarity(user_a, user_b)
    return interaction_score * 2 + similarity_score
