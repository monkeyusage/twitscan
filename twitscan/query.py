from __future__ import annotations

from typing import TypedDict

from twitscan import session
from twitscan.models import Entourage, TwitscanStatus, TwitscanUser
from twitscan.scanner import check_user_id


class CacheRecord(TypedDict):
    entourage: set[int]
    hashtags: set[str]

cache: dict[int, CacheRecord] = {}


def user_by_screen_name(screen_name: str) -> TwitscanUser | None:
    user: TwitscanUser | None = (
        session.query(TwitscanUser)
        .filter(TwitscanUser.screen_name == screen_name)
        .one_or_none()
    )
    return user


def user_by_id(user_id: int) -> TwitscanUser | None:
    user: TwitscanUser | None = (
        session.query(TwitscanUser)
        .filter(TwitscanUser.user_id == user_id)
        .one_or_none()
    )
    return user


def status_by_id(status_id: int) -> TwitscanStatus | None:
    status: TwitscanStatus | None = (
        session.query(TwitscanStatus)
        .filter(TwitscanStatus.status_id == status_id)
        .one_or_none()
    )
    return status


def statuses_by_hashtag(hashtag: str) -> list[TwitscanStatus]:
    statuses: list[TwitscanStatus] = (
        session.query(TwitscanStatus)
        .filter(hashtag in map(lambda ht: ht.hashtag_name, TwitscanStatus.hashtags))
        .all()
    )
    return statuses


def statuses(string: str) -> list[TwitscanStatus]:
    statuses: list[TwitscanStatus] = (
        session.query(TwitscanStatus)
        .filter(TwitscanStatus.text.like(f"%{string}%"))
        .all()
    )
    return statuses


def followers(user_id: int) -> list[TwitscanUser]:
    entourage = (
        session.query(Entourage)
        .filter(Entourage.user_id == user_id and Entourage.follower)
        .all()
    )
    followers_ids = set(map(lambda ent: ent.friend_follower_id, entourage))
    follower_users: list[TwitscanUser] = (
        session.query(TwitscanUser)
        .filter(TwitscanUser.user_id.in_(followers_ids))
        .all()
    )
    return follower_users


def users(name: str) -> list[TwitscanUser]:
    usrs: list[TwitscanUser] = (
        session.query(TwitscanUser)
        .filter(TwitscanUser.screen_name.like(f"%{name}%"))
        .all()
    )
    return usrs


def hashtags_used(user: TwitscanUser) -> set[str]:
    used: set[str] = set()
    for status in user.chirps:
        for hashtag in status.hashtags:
            used.add(hashtag.hashtag_name)
    return used


def n_mentions(user: TwitscanUser, target_id: int) -> tuple[int, int]:
    mention_counter = 0
    total_mentions = 0
    for status in user.chirps:
        for mention in status.user_mentions:
            if mention.user_id == target_id:
                mention_counter += 1
            total_mentions += 1
    return mention_counter, total_mentions


def n_interactions(user: TwitscanUser, target_user: int) -> tuple[int, int, int]:
    fav, retweet, comment = 0, 0, 0
    for interaction in user.interacted_tweets:
        maybe_status: None | TwitscanStatus = (
            session.query(TwitscanStatus)
            .filter(TwitscanStatus.status_id == interaction.status_id)
            .one_or_none()
        )
        if maybe_status is None:
            continue
        if maybe_status.user_id == target_user:
            if interaction.fav:
                fav += 1
            if interaction.retweet:
                retweet += 1
            if interaction.comment:
                comment += 1
    return fav, retweet, comment, rt_counter, comment_counter


def proximity(user_a: TwitscanUser, user_b: TwitscanUser) -> tuple[float, ...]:
    """
    computes proximity score between two users, stores user a general information inside cache
    """
    global cache
    for user in (user_a, user_b):
        assert check_user_id(user.user_id) is not None, f"User {user} not in db"

    if cache.get(user_a.user_id) is None:
        entourage_a = set(map(lambda ent: ent.friend_follower_id, user_a.entourage))
        hashtags_a = hashtags_used(user_a)
        cache[user_a.user_id] = CacheRecord(entourage=entourage_a, hashtags=hashtags_a)
    else:
        cr = cache[user_a.user_id]
        entourage_a = cr["entourage"]
        hashtags_a = cr["hashtags"]

    a_mentions_b, a_mentions_counter = n_mentions(user_a, user_b.user_id)
    a_favs_b, a_rt_b, a_cmt_b = n_interactions(user_a, user_b.user_id)

    entourage_b = set([ent.friend_follower_id for ent in user_b.entourage])
    hashtags_b = hashtags_used(user_b)
    b_mentions_a, b_mentions_counter = n_mentions(user_b, user_a.user_id)
    b_favs_a, b_rt_a, b_cmt_a = n_interactions(user_b, user_a.user_id)

    ent_a_len = len(entourage_a)
    ent_b_len = len(entourage_b)
    ent_len = ent_b_len + ent_a_len

    hash_a_len = len(hashtags_a)
    hash_b_len = len(hashtags_b)
    hash_len = hash_b_len + hash_a_len
    # weigh common entourage / hashtags by number of entourage acquired / hashtags used
    common_entourage = len(entourage_a.intersection(entourage_b)) / ent_len if ent_len != 0 else 0
    common_hashtags = len(hashtags_a.intersection(hashtags_b)) / hash_len if hash_len != 0 else 0

    total_mentions = a_mentions_b + b_mentions_a
    total_favs = a_favs_b + b_favs_a
    total_rts = a_rt_b + b_rt_a
    total_cmts = a_cmt_b + b_cmt_a

    return (
        a_mentions_b,
        b_mentions_a,
        a_favs_b,
        b_favs_a,
        a_rt_b,
        b_rt_a,
        a_cmt_b,
        b_cmt_a,
        ent_a_len,
        ent_len,
        hash_a_len,
        hash_b_len,
        hash_len,
        common_entourage,
        len(entourage_a),
        len(entourage_b),
        common_hashtags,
        len(hashtags_a),
        len(hashtags_b),
        a_mentions_b,
        b_mentions_a,
        a_mentions_counter,
        b_mentions_counter,
        a_favs_b,
        b_favs_a,
        user_a.favorites_count,
        user_b.favorites_count,
        a_rt_b,
        b_rt_a,
        a_cmt_b,
        b_cmt_a,
    )


def db_info() -> dict[str, int]:
    """
    count for each table, return dictionnary of counts
    """

    def count(table: str) -> int:
        stmt = f"SELECT COUNT(*) FROM {table}"
        cursor = session.execute(stmt)
        result: tuple[int, ...] | None = cursor.fetchone()
        return result[0] if result is not None else 0

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
