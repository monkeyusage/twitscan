from __future__ import annotations
import asyncio

from twitscan import async_session as session
from typing import Awaitable, AsyncGenerator, Callable
from twitscan.models import TwitscanUser
from twitscan.engagement import EngagementScore


async def followers(user_id: int) -> AsyncGenerator[int, None]:
    stmt = f"""
        SELECT user.user_id FROM user
        JOIN friend ON user.user_id = friend.friend_follower_id
        WHERE (friend.user_id == {user_id}) AND (friend.follower IS TRUE)
    """
    async with session.execute(stmt) as cursor:
        async for follower in cursor:
            yield follower


async def friends(user_id: int) -> AsyncGenerator[int, None]:
    stmt = f"""
        SELECT user_id FROM user
        JOIN friend ON user.user_id = friend.friend_follower_id
        WHERE (friend.user_id == {user_id}) AND (friend.friend IS TRUE)
    """
    async with session.execute(stmt) as cursor:
        async for friend in cursor:
            yield friend


async def entourage(user_id: int) -> AsyncGenerator[int, None]:
    stmt = f"""
        SELECT user_id FROM user
        JOIN friend ON user.user_id = friend.friend_follower_id
        WHERE friend.user_id == {user_id}
    """
    async with session.execute(stmt) as cursor:
        async for ent in cursor:
            yield ent


async def hashtags(user_id: int) -> AsyncGenerator[str, None]:
    """takes user and returns used hashtags"""
    stmt = f"""
        SELECT hashtag_name FROM hashtag
        JOIN status ON status.status_by_id = hashtag.status_id
        WHERE status.user_id == {user_id}
    """
    async with session.execute(stmt) as cursor:
        async for result in cursor:
            yield result


def common_items_maker(generator: AsyncGenerator):
    async def common_func(user_a: TwitscanUser, user_b: TwitscanUser):
        a_set: set[int] = set()
        common_list: list[int] = []
        async for item in generator(user_a):
            a_set.add(item)
        async for item in generator(user_b):
            if item in a_set:
                common_list.append(item)
        return common_list

    return common_func


common_entourage = common_items_maker(entourage)
common_followers = common_items_maker(followers)
common_friends = common_items_maker(friends)
common_hashtags = common_items_maker(hashtags)


def table_generator_maker(table) -> Callable:
    async def table_generator() -> AsyncGenerator[tuple, None]:
        stmt = f"SELECT * FROM {table}"
        async with session.execute(stmt) as cursor:
            async for item in cursor:
                yield item

    return table_generator


all_users = table_generator_maker("user")
all_statuses = table_generator_maker("status")
all_interactions = table_generator_maker("interaction")
all_entourages = table_generator_maker("friend")
all_mentions = table_generator_maker("mention")
all_links = table_generator_maker("link")
all_hashtags = table_generator_maker("hashtag")


async def user_by_screen_name(screen_name: str) -> Awaitable[tuple | None]:
    result = await session.execute(
        f"""
        SELECT * FROM user
        WHERE user.screen_name = '{screen_name}'
    """
    )
    user = await result.fetchone()
    return user


async def user_by_id(user_id: int) -> Awaitable[tuple | None]:
    result = await session.execute(
        f"""
        SELECT * FROM user
        WHERE user.user_id = '{user_id}'
    """
    )
    user = await result.fetchone()
    return user


async def status_by_id(status_id: int) -> Awaitable[tuple | None]:
    result = await session.execute(
        f"""
        SELECT * FROM status
        WHERE status.status_id == '{status_id}'
    """
    )
    status = await result.fetchone()
    return status


async def statuses_by_hashtag(hashtag: str) -> AsyncGenerator[tuple | None]:
    stmt = f"""
        SELECT * FROM hashtag
        JOIN status on hashtag.status_id = status.status_id 
        WHERE hashtag.hashtag_name = '{hashtag}'
    """
    async with session.execute(stmt) as cursor:
        async for status in cursor:
            yield status


async def statuses(string: str) -> AsyncGenerator[tuple, None]:
    stmt = f"""
        SELECT * FROM status
        WHERE status.text LIKE '%{string}%'
    """
    async with session.execute(stmt) as cursor:
        async for status in cursor:
            yield status


async def users(name: str) -> AsyncGenerator[tuple, None]:
    stmt = f"""
        SELECT * FROM user
        WHERE user.screen_name LIKE '%{name}%'
    """
    async with session.execute(stmt) as cursor:
        async for item in cursor:
            yield item


async def similarity_for(
    follower_id: int, target_user_id: int
) -> Awaitable[tuple | None]:
    """
    computes similarity score for follower towards target_user
    returns: user_id, n_friends, n_followers (in common)
    """
    preprocess = f"""
        DROP TABLE IF EXISTS tmp_followers;
        DROP TABLE IF EXISTS tmp_followers_followers;

        CREATE TEMP TABLE tmp_followers AS 
        SELECT friend.user_id as f_id
        FROM friend
        WHERE friend.friend_follower_id = '{target_user_id}';

        CREATE TEMP TABLE tmp_followers_followers AS
        SELECT * FROM tmp_followers
        LEFT JOIN friend ON friend.user_id = tmp_followers.f_id
        WHERE friend.friend_follower_id = '{follower_id}';
    """

    stmt = """
        SELECT SUM(friend) AS n_friends, SUM(follower) AS n_followers 
        FROM tmp_followers_followers
        INNER JOIN tmp_followers ON tmp_followers.f_id = tmp_followers_followers.friend_follower_id
        GROUP BY tmp_followers.f_id
    """

    await session.executescript(preprocess)
    cursor = await session.execute(stmt)
    result = await cursor.fetchone()
    return result


async def interactions_for(target_user_id: int) -> AsyncGenerator[tuple, None]:
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
    cursor = await session.execute(stmt)
    results = await cursor.fetchall()
    for item in results:
        yield item


async def engagement_for(target_user_id: int) -> AsyncGenerator[EngagementScore, None]:
    """computes the engagement twoards user_b :=> the higher the more engagement"""
    async for interaction in interactions_for(target_user_id):
        follower_id, n_likes, n_comments, n_retweets, n_mentions = interaction
        sim_score = await similarity_for(follower_id, target_user_id)
        n_friends, n_followers = sim_score if sim_score else (None, None)
        yield EngagementScore(
            follower_id, target_user_id, n_friends, n_followers, n_likes, n_comments, n_retweets, n_mentions
        )


def db_info() -> dict[str, int]:
    """
    synchronously request count for each table, return dictionnary of counts
    """

    async def async_count(table: str) -> Awaitable[int]:
        stmt = f"SELECT COUNT(*) FROM {table}"
        cursor = await session.execute(stmt)
        result = await cursor.fetchone()
        return result[0]

    count = lambda table: asyncio.get_event_loop().run_until_complete(
        async_count(table)
    )
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
