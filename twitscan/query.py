from typing import List, Set
from twitscan.models import TwitscanUser


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
