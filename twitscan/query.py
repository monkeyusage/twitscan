from __future__ import annotations
from collections import namedtuple

from twitscan import session
from sqlalchemy import select
from typing import Callable, Iterator
from twitscan.models import (
    Entourage,
    Hashtag,
    Interaction,
    Link,
    Mention,
    TwitscanStatus,
    TwitscanUser,
)


def followers(user: TwitscanUser) -> Iterator[TwitscanUser]:
    stmt = (
        select(TwitscanUser)
        .join(Entourage, TwitscanUser.user_id == Entourage.friend_follower_id)
        .where(Entourage.user_id == user.user_id and Entourage.follower)
    )
    results = session.execute(stmt)
    for follower in results:
        yield follower.TwitscanUser


def friends(user: TwitscanUser) -> Iterator[TwitscanUser]:
    stmt = (
        select(TwitscanUser)
        .join(Entourage, TwitscanUser.user_id == Entourage.friend_follower_id)
        .where(Entourage.user_id == user.user_id and Entourage.friend)
    )
    results = session.execute(stmt)
    for follower in results:
        yield follower.TwitscanUser


def entourage(user: TwitscanUser) -> Iterator[TwitscanUser]:
    stmt = (
        select(TwitscanUser)
        .join(Entourage, TwitscanUser.user_id == Entourage.friend_follower_id)
        .where(Entourage.user_id == user.user_id)
    )
    results = session.execute(stmt)
    for ent in results:
        yield ent.TwitscanUser

def hashtags(user: TwitscanUser) -> Iterator[Hashtag]:
    """takes user and returns used hashtags"""
    results = session.execute(
        select(Hashtag)
        .join(TwitscanStatus)
        .where(TwitscanStatus.user_id == user.user_id)
    )
    for result in results:
        yield result.Hashtag


CommonMaker : Callable[[TwitscanUser, TwitscanUser], list[TwitscanUser]]

def common_items_maker(generator : Iterator[TwitscanUser]) -> CommonMaker:
    def common_func(user_a:TwitscanUser, user_b:TwitscanUser) -> list[TwitscanUser]:
        a_set : set[TwitscanUser] = set(item for item in generator(user_a))
        common_list : list[TwitscanUser] = [item for item in generator(user_b) if item in a_set]
        return common_list
    return common_func

common_entourage : CommonMaker = common_items_maker(entourage)
common_followers : CommonMaker = common_items_maker(followers)
common_friends : CommonMaker = common_items_maker(friends)
common_hashtags : CommonMaker = common_items_maker(hashtags)

def table_generator_maker(table) -> Callable[[], Iterator]:
    def table_generator() -> Iterator:
        items  = session.execute(select(table))
        for item in items:
            yield item._data[0]
    return table_generator

all_users : Iterator[TwitscanUser] = table_generator_maker(TwitscanUser)
all_statuses : Iterator[TwitscanStatus] = table_generator_maker(TwitscanStatus)
all_interactions : Iterator[Interaction] = table_generator_maker(Interaction)
all_entourages : Iterator[Entourage] = table_generator_maker(Entourage)
all_mentions : Iterator[Mention] = table_generator_maker(Mention)
all_links : Iterator[Link] = table_generator_maker(Link)
all_hashtags : Iterator[Hashtag] = table_generator_maker(Hashtag)


def user_by_screen_name(screen_name: str) -> TwitscanUser | None:
    result  = session.execute(
        select(TwitscanUser).where(TwitscanUser.screen_name == screen_name)
    ).first()
    if result:
        return result.TwitscanUser
    return


def user_by_id(user_id: int) -> TwitscanUser | None:
    result  = session.execute(
        select(TwitscanUser).where(TwitscanUser.user_id == user_id)
    ).first()
    if result:
        return result.TwitscanUser
    return


def status_by_id(status_id: int) -> TwitscanStatus | None:
    result  = session.execute(
        select(TwitscanStatus).where(TwitscanStatus.status_id == status_id)
    ).first()
    if result:
        return result.TwitscanStatus
    return


def statuses_by_hashtag(hashtag: str) -> Iterator[TwitscanStatus]:
    results = session.execute(
        select(Hashtag).join(TwitscanStatus).where(Hashtag.hashtag_name == hashtag)
    )
    for result in results:
        yield result.Hashtag.status


def find_status(string: str) -> list[TwitscanStatus]:
    string = "%" + string + "%"
    stmt = select(TwitscanStatus).where(TwitscanStatus.text.ilike(string))
    statuses = session.execute(stmt)
    return [s.TwitscanStatus for s in statuses.fetchall()]


def find_user(name: str) -> list[TwitscanUser]:
    name = "%" + name + "%"
    stmt = select(TwitscanUser).where(TwitscanUser.screen_name.ilike(name))
    users = session.execute(stmt)
    return [u.TwitscanUser for u in users.fetchall()]
    
SimilarityValues = namedtuple('SimilarityValues', ['c_ht', 'c_fol', 'c_fri'])
SimilarityScore : dict[TwitscanUser, tuple[int, int, int]]

def similarity_for(target_user: TwitscanUser) -> Iterator[SimilarityScore]:
    '''computes similarity score for all users towards target_user'''
    stmt = f''' '''
    similarities_result = session.execute(stmt)
    similarities : SimilarityScore = dict((
        result.user_id, (result.common_ht, result.common_followers, result.common_friends)
    ) for result in similarities_result)
    for user in followers(target_user):
        score = similarities.get(user.user_id, (0, 0, 0))
        similarity : SimilarityValues = SimilarityValues(score[0])
        yield {user:similarity} # assuming all have same weight

InteractionValues = namedtuple('InteractionValues', ['n_likes', 'n_comments', 'n_retweets'])
InteractionScore : dict[TwitscanUser, InteractionValues]

def interactions_for(target_user: TwitscanUser) -> Iterator[InteractionScore]:
    '''computes all the interactions from followers to target_user
        :=> the higher the more interaction
    generator to get all interactions
    '''
    stmt = f'''
        SELECT 
            user_id,
            SUM(fav) AS n_likes,
            SUM(comment) AS n_comments,
            SUM(retweet) AS n_retweets
        FROM (
            SELECT 
                user.user_id,
                interaction.*,
                status.user_id
            FROM user
            LEFT JOIN interaction ON user.user_id = interaction.user_id
            LEFT JOIN status ON interaction.status_id = status.status_id
            WHERE status.user_id = {target_user.user_id}
        )
        GROUP BY user_id
    '''
    interactions_result  = session.execute(stmt)
    interactions : InteractionScore = dict((
        result.user_id, (result.n_likes, result.n_comments, result.n_retweets)
    ) for result in interactions_result)
    for user in followers(target_user):
        score = interactions.get(user.user_id, (0, 0, 0))
        values = InteractionValues(n_likes=score[0], n_comments=score[1], n_retweets=score[2])
        yield {user: values}

EngagementScore : dict[TwitscanUser, int]

def engagement_for(target_user: TwitscanUser) -> EngagementScore:
    """computes the engagement of user_a towards user_b :=> the higher the more engagement"""
    engagements : EngagementScore = {}
    for interaction, similarity in zip(interactions_for(target_user), ):
        ...
    interaction_score: InteractionScore = interactions_for(target_user)
    
    similarity_score: SimilarityScore = similarity_for(target_user)
    return interaction_score * 2 + similarity_score


def db_info() -> dict[str, int]:
    count = lambda table: session.execute(f'SELECT COUNT(*) FROM {table}').first()[0]
    info = {
        'user': count('user'),
        'entourage': count('friend'),
        'interaction': count('interaction'),
        'status': count('status'),
        'mention': count('mention'),
        'urls': count('link'),
        'hashtags': count('hashtag'),
    }
    return info
