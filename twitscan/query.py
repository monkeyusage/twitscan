from typing import List, Set
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


def followers(user: TwitscanUser) -> List[int]:
    return list(
        map(
            lambda e: e.friend_follower_id,
            filter(lambda e: e.follower, user.entourage),
        )
    )


def friends(user: TwitscanUser) -> List[int]:
    return list(
        map(
            lambda e: e.friend_follower_id,
            filter(lambda e: e.friend, user.entourage),
        )
    )


def entourage(user: TwitscanUser) -> List[int]:
    return list(map(lambda e: e.e.friend_follower_id, user.entourage))


def common_followers(user_a: TwitscanUser, user_b: TwitscanUser) -> Set[int]:
    followers_a: Set[int] = set(followers(user_a))
    followers_b: Set[int] = set(followers(user_b))
    return followers_a & followers_b


def common_friends(user_a: TwitscanUser, user_b: TwitscanUser) -> Set[int]:
    friends_a: Set[int] = set(friends(user_a))
    friends_b: Set[int] = set(friends(user_b))
    return friends_a & friends_b


def common_entourage(user_a: TwitscanUser, user_b: TwitscanUser) -> Set[int]:
    entourage_a: Set[int] = set(entourage(user_a))
    entourage_b: Set[int] = set(entourage(user_b))
    return entourage_a & entourage_b


def all_users() -> List[TwitscanUser]:
    return session.query(TwitscanUser).all()


def all_statuses() -> List[TwitscanStatus]:
    return session.query(TwitscanStatus).all()


def all_interations() -> List[Interaction]:
    return session.query(Interaction).all()


def all_entourages() -> List[Entourage]:
    return session.query(Entourage).all()


def all_mentions() -> List[Mention]:
    return session.query(Mention).all()


def all_links() -> List[Link]:
    return session.query(Link).all()


def all_hashtags() -> List[Hashtag]:
    return session.query(Hashtag).all()


def by_screen_name(screen_name: str) -> TwitscanUser:
    """queries user by screen name"""
    return (
        session.query(TwitscanUser)
        .filter(TwitscanUser.screen_name == screen_name)
        .first()
    )


def hashtags_used(user: TwitscanUser) -> Set[Hashtag]:
    """takes user and returns used hashtags"""
    used_ht: Set[Hashtag] = set()
    for chirp in user.chirps:
        hashtags = list(map(lambda hashtag: hashtag.hashtag_name, chirp.hashtags))
        used_ht.update(hashtags)
    return used_ht
