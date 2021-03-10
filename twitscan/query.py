from __future__ import annotations
from twitscan import session
from twitscan.models import (
    Entourage,
    Hashtag,
    Interaction,
    Link,
    Mention,
    TwitscanStatus,
    TwitscanUser,
)


def followers(user: TwitscanUser) -> list[int]:
    return list(
        map(
            lambda e: e.friend_follower_id,
            filter(lambda e: e.follower, user.entourage),
        )
    )


def friends(user: TwitscanUser) -> list[int]:
    return list(
        map(
            lambda e: e.friend_follower_id,
            filter(lambda e: e.friend, user.entourage),
        )
    )


def entourage(user: TwitscanUser) -> list[int]:
    return list(map(lambda e: e.e.friend_follower_id, user.entourage))


def common_followers(user_a: TwitscanUser, user_b: TwitscanUser) -> set[int]:
    followers_a: set[int] = set(followers(user_a))
    followers_b: set[int] = set(followers(user_b))
    return followers_a & followers_b


def common_friends(user_a: TwitscanUser, user_b: TwitscanUser) -> set[int]:
    friends_a: set[int] = set(friends(user_a))
    friends_b: set[int] = set(friends(user_b))
    return friends_a & friends_b


def common_entourage(user_a: TwitscanUser, user_b: TwitscanUser) -> set[int]:
    entourage_a: set[int] = set(entourage(user_a))
    entourage_b: set[int] = set(entourage(user_b))
    return entourage_a & entourage_b


def all_users() -> list[TwitscanUser]:
    return session.query(TwitscanUser).all()


def all_statuses() -> list[TwitscanStatus]:
    return session.query(TwitscanStatus).all()


def all_interations() -> list[Interaction]:
    return session.query(Interaction).all()


def all_entourages() -> list[Entourage]:
    return session.query(Entourage).all()


def all_mentions() -> list[Mention]:
    return session.query(Mention).all()


def all_links() -> list[Link]:
    return session.query(Link).all()


def all_hashtags() -> list[Hashtag]:
    return session.query(Hashtag).all()


def user_by_screen_name(screen_name: str) -> TwitscanUser | None:
    """queries user by screen name"""
    return (
        session.query(TwitscanUser)
        .filter(TwitscanUser.screen_name == screen_name)
        .first()
    )


def user_by_id(user_id: int) -> TwitscanUser | None:
    return (
        session.query(TwitscanUser)
        .filter(TwitscanUser.user_id == user_id)
        .first()
    )

def hashtags_used(user: TwitscanUser) -> set[Hashtag]:
    """takes user and returns used hashtags"""
    used_ht: set[Hashtag] = set()
    for chirp in user.chirps:
        hashtags = list(map(lambda hashtag: hashtag.hashtag_name, chirp.hashtags))
        used_ht.update(hashtags)
    return used_ht


def status_by_status_id(status_id: int) -> TwitscanStatus | None:
    return (
        session.query(TwitscanStatus)
        .filter(TwitscanStatus.status_id == status_id)
        .first()
    )


def statuses_by_hashtag(hashtag: str) -> list[TwitscanStatus]:
    hashtags = session.query(Hashtag).filter(Hashtag.hashtag_name == hashtag).all()
    return list(map(lambda ht: ht.status, hashtags))


def find_status(string: str) -> list[TwitscanStatus]:
    string = "%" + string + "%"
    return session.query(TwitscanStatus).filter(TwitscanStatus.text.ilike(string)).all()


def find_user(name: str) -> list[TwitscanUser]:
    name = "%" + name + "%"
    return (
        session.query(TwitscanUser).filter(TwitscanUser.screen_name.ilike(name)).all()
    )
