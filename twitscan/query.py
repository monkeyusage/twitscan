from __future__ import annotations

from tweepy.models import Model
from twitscan.models import TwitscanUser
from twitscan.scanner import check_user

from twitscan import session
from typing import Iterator, Callable, Iterable, Any, TypeVar
T = TypeVar("T")

def followers(user_id: int) -> list[tuple[int]]:
    stmt = f"""
        SELECT friend_follower_id FROM friend
        WHERE (user_id == {user_id}) AND (follower IS TRUE)
    """
    cursor = session.execute(stmt)
    return cursor.fetchall()


def friends(user_id: int) -> list[tuple[int]]:
    stmt = f"""
        SELECT friend_follower_id FROM friend
        WHERE (user_id == {user_id}) AND (friend IS TRUE)
    """
    cursor = session.execute(stmt)
    return cursor.fetchall()


def entourage(user_id: int) -> list[tuple[int]]:
    stmt = f"""
        SELECT friend_follower_id FROM friend
        WHERE user_id == {user_id}
    """
    cursor = session.execute(stmt)
    return cursor.fetchall()


def hashtags(user_id: int) -> list[tuple[str]]:
    """takes user and returns used hashtags"""
    stmt = f"""
        SELECT hashtag_name FROM hashtag
        JOIN status ON status.status_by_id = hashtag.status_id
        WHERE status.user_id == {user_id}
    """
    cursor = session.execute(stmt)
    return cursor.fetchall()


def common_items_maker(func: Callable[[int], list[tuple[T]]]):
    def common_func(user_a: int, user_b: int) -> list[T]:
        a_set: set[T] = set()
        common_list: list[T] = []
        for item in func(user_a):
            a_set.add(item[0])
        for item in func(user_b):
            if item in a_set:
                common_list.append(item[0])
        return common_list
    return common_func


common_entourage = common_items_maker(entourage)
common_followers = common_items_maker(followers)
common_friends = common_items_maker(friends)
common_hashtags = common_items_maker(hashtags)

def all_users():
    return session.query(TwitscanUser).all()

def all_statuses():
    return session.query(TwitscanUser).all()

def all_users():
    return session.query(TwitscanUser).all()
def all_users():
    return session.query(TwitscanUser).all()
def all_users():
    return session.query(TwitscanUser).all()
all_users = table_maker("user")
all_statuses = table_maker("status")
all_interactions = table_maker("interaction")
all_entourages = table_maker("friend")
all_mentions = table_maker("mention")
all_links = table_maker("link")
all_hashtags = table_maker("hashtag")

def user_by_screen_name(screen_name: str) -> TwitscanUser | None:
    user = (
        session
        .query(TwitscanUser)
        .filter(TwitscanUser.screen_name == screen_name)
        .one_or_none()
    )
    return user


def user_by_id(user_id: int) -> tuple | None:
    result = session.execute(
        f"""
        SELECT * FROM user
        WHERE user_id = '{user_id}'
    """
    )
    user = result.fetchone()
    return user


def status_by_id(status_id: int) -> tuple | None:
    result = session.execute(
        f"""
        SELECT * FROM status
        WHERE status_id == '{status_id}'
    """
    )
    status = result.fetchone()
    return status


def statuses_by_hashtag(hashtag: str) -> Iterable[tuple]:
    stmt = f"""
        SELECT * FROM hashtag
        JOIN status on hashtag.status_id = status.status_id 
        WHERE hashtag.hashtag_name = '{hashtag}'
    """
    cursor = session.execute(stmt)
    return cursor.fetchall()


def statuses(string: str) -> Iterable[tuple]:
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


def similarity(follower_id: int, target_user_id: int) -> int | None:
    """
    computes similarity score for follower towards target_user
    returns: user_id, n_friends, n_followers (in common)
    """
    for user_id in (follower_id, target_user_id):
        if check_user(user_id=user_id) is None:
            print("One user is not in database")
            return None
    entourage_sum = len(common_entourage(follower_id, target_user_id))
    hashtags_sum = len(common_hashtags(follower_id, target_user_id))
    
    return entourage_sum + hashtags_sum


def popularity(target_user_id: int) -> list[tuple]:
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
    return cursor.fetchall()


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
