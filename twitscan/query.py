from __future__ import annotations

from typing import Iterable, Iterator

from twitscan import session
from twitscan.models import TwitscanStatus, TwitscanUser
from twitscan.scanner import check_user_id


def user_by_screen_name(screen_name: str) -> TwitscanUser | None:
    user = (
        session.query(TwitscanUser)
        .filter(TwitscanUser.screen_name == screen_name)
        .one_or_none()
    )
    return user


def user_by_id(user_id: int) -> TwitscanUser | None:
    user = (
        session.query(TwitscanUser)
        .filter(TwitscanUser.user_id == user_id)
        .one_or_none()
    )
    return user


def status_by_id(status_id: int) -> tuple | None:
    status = (
        session.query(TwitscanStatus)
        .filter(TwitscanStatus.status_id == status_id)
        .one_or_none()
    )
    return status


def statuses_by_hashtag(hashtag: str) -> list[tuple]:
    stmt = f"""
        SELECT * FROM hashtag
        JOIN status on hashtag.status_id = status.status_id 
        WHERE hashtag.hashtag_name = '{hashtag}'
    """
    cursor = session.execute(stmt)
    return cursor.fetchall()


def statuses(string: str) -> list[tuple]:
    stmt = f"""
        SELECT * FROM status
        WHERE status.text LIKE '%{string}%'
    """
    cursor = session.execute(stmt)
    return cursor.fetchall()


def users(name: str) -> Iterator[tuple]:
    stmt = f"""
        SELECT * FROM user
        WHERE user.screen_name LIKE '%{name}%'
    """
    cursor = session.execute(stmt)
    for item in cursor:
        yield item

def hashtags_used(user:TwitscanUser) -> set[str]:
    used = set()
    for status in user.chirps:
        for hashtag in status.hashtags:
            used.add(hashtag.hashtag_name)
    return used

def n_mentions(user:TwitscanUser, target_id:int) -> int:
    counter = 0
    for status in user.chirps:
        for mention in status.user_mentions:
            if mention.user_id == target_id:
                counter += 1
    return counter

def proximity(user_a: TwitscanUser, user_b: TwitscanUser) -> int:
    """
    computes similarity score for follower towards target_user
    returns: size of common entourage (in common)
    """
    total_score = 0
    for user in (user_a, user_b):
        assert check_user_id(user_a) is not None, f"User {user} not in db"
    
    entourage_a = set([ent.friend_follower_id for ent in user_a.entourage])
    hashtags_a = hashtags_used(user_a)
    a_mentions_b = n_mentions(user_a, user_b.user_id)

    entourage_b = set([ent.friend_follower_id for ent in user_b.entourage])
    hashtags_b = hashtags_used(user_b)
    b_mentions_a = n_mentions(user_b, user_a.user_id)

    common_entourage = len(entourage_a.intersection(entourage_b))
    common_hashtags = len(hashtags_a.intersection(hashtags_b))
    total_mentions = a_mentions_b + b_mentions_a


    return 


def db_info() -> dict[str, int | None]:
    """
    count for each table, return dictionnary of counts
    """

    def count(table: str) -> int | None:
        stmt = f"SELECT COUNT(*) FROM {table}"
        cursor = session.execute(stmt)
        result = cursor.fetchone()
        return result[0]

    info = {
        "user": count("user"),
        "entourage": count("friend"),
        "interaction": count("interaction"),
        "status": count("status"),
        "mention": count("mention"),
        "urls": count("link"),
        "hashtags": count("hashtag"),
    }
    return info
