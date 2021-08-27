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


def similarity(user_a: TwitscanUser, user_b: TwitscanUser) -> int:
    """
    computes similarity score for follower towards target_user
    returns: size of common entourage (in common)
    """
    for user in (user_a, user_b):
        assert check_user_id(user_a) is not None, f"User {user} not in db"

    ent_a = set([ent.friend_follower_id for ent in user_a.entourage])
    ent_b = set([ent.friend_follower_id for ent in user_b.entourage])

    return len(ent_a.intersection(ent_b))


def popularity(target_user_id: int) -> int:
    """
    retrieves all interactions towarded to target_user from database (except self interaction)
    yields user_id, SUM(likes), SUM(comments), SUM(retweets), COUNT(mentions)
    """
    stmt = f"""
        SELECT 
            user_id,
            SUM(fav) AS n_likes,
            SUM(comment) AS n_comments,
            SUM(retweet) AS n_retweets,
            COUNT(m_user_id) AS n_mentions
        FROM (
            SELECT 
                user.user_id,
                interaction.*,
                status.user_id,
                mention.user_id AS m_user_id
            FROM user
            LEFT JOIN interaction ON user.user_id = interaction.user_id
            LEFT JOIN status ON interaction.status_id = status.status_id
            LEFT JOIN mention ON mention.status_id = status.status_id
            WHERE status.user_id = '{target_user_id}' AND user.user_id != status.user_id
        )
        GROUP BY user_id
    """
    cursor = session.execute(stmt)
    ret = cursor.fetchall()
    return ret


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
