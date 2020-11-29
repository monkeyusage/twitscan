import logging
from tweepy.models import User as RawUser
from twitscan import api, session, config
from twitscan.models import Entourage, Interaction, User
from twitscan import status
from twitscan.errors import UserProtectedError

from typing import Optional, Set, List

def check_user(screen_name: Optional[str] = None, user_id: Optional[int] = None) -> Optional[User]:
    """Checks if user is in database, if so returns it otherwise returns None"""
    if screen_name:
        user: Optional[User] = (
            session.query(User)
            .filter(User.screen_name == screen_name)
            .one_or_none()
        )
    else:
        user = session.query(User).filter(User.user_id == user_id).one_or_none()
    if user is not None:
        return user
    return None

def scan_twitter(user_id: Optional[int], screen_name: Optional[str]) -> None:
    """Fetches user from twitter, Saves it in db and queries db for user"""
    # fetch user from twitter
    user: RawUser = (
        api.get_user(screen_name=screen_name)
        if screen_name
        else api.get_user(user_id=user_id)
    )
    if user.protected:
        raise UserProtectedError(f"User {user.screen_name} is protected")
    save(user)  # add user to database
    
def scan(user_id: Optional[int], screen_name: Optional[str]) -> User:
    """Checks if user is already scanned, if so retrieves user else scans user from twitter"""
    assert not (
        (user_id is None) and (screen_name is None)
    ), "Both identifiers for User are None"

    user: Optional[User] = check_user(
        user_id=user_id, screen_name=screen_name
    )
    if user is None:
        logging.info(
            f"Scanning user : {screen_name if screen_name else user_id} from twitter"
        )
        db_user: User = TwitterUser._scan_twitter(
            user_id=user_id, screen_name=screen_name
        )
        return db_user
    else:
        logging.info(
            f"User {user.screen_name} already in database, scanning from db"
        )
        return user

def add_entouage(user: RawUser) -> None:
    """Calls twitter api to get friends and followers
    Pushes those ids in user's entourage
    """
    logging.debug(f"Fetching friends (followees) for {user.screen_name}")
    friends: Set[int] = set(api.friends_ids(user.id))
    logging.debug(f"Fetching followers for {user.screen_name}")
    followers: Set[int] = set(api.followers_ids(user.id))

    friends_followers = followers | friends
    persons: List[Entourage] = []
    for ff in friends_followers:
        is_friend = ff in friends
        is_follower = ff in followers
        person: Entourage = Entourage(
            user_id=user.id,
            friend_follower_id=ff,
            friend=is_friend,
            follower=is_follower,
        )
        persons.append(person)

    session.add_all(persons)

def _add_interactions(user: RawUser) -> None:
    """Uses twitter api to get latest tweets and retweets / comments / likes
    Stores user's related interactions in database
    """
    logging.debug(f"Fetching tweets for {user.screen_name}")
    chirps: List[TwitterStatus] = [
        TwitterStatus(status)
        for status in api.user_timeline(
            screen_name=user.screen_name,
            count=config["MAX_TWEETS"],
            include_rts=True,
            tweet_mode="extended",
        )
    ]

    logging.debug(f"Fetching favorites for {user.screen_name}")
    liked: Set[int] = set(
        [TwitterStatus(tweet).id for tweet in api.favorites(user.screen_name)]
    )

    retweeted: Set[int] = set([chirp.id for chirp in chirps if chirp.is_retweet])
    comments: Set[int] = set(
        [chirp.id for chirp in chirps if chirp.in_reply_to_status_id]
    )

    statuses = liked | retweeted | comments
    interactions: List[Interaction] = []
    for status in statuses:
        is_like = status in liked
        is_retweet = status in retweeted
        is_comment = status in comments
        interaction = Interaction(
            user_id=user.id,
            status_id=status,
            like=is_like,
            retweet=is_retweet,
            comment=is_comment,
        )
        interactions.append(interaction)

    session.add_all(interactions)


def save(user:RawUser, debug_mode:bool=False) -> None:
    if debug_mode:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    """Uses Tweepy User to create and push user info to db"""
    logging.debug(f"Adding {user.screen_name} to database")
    user_info: User = User(
        user_id=user.id,
        screen_name=user.screen_name,
        created_at=user.created_at,
        verified=user.verified,
        favorites_count=user.favourites_count,
        status_count=user.statuses_count,
        friends_count=user.friends_count,
        followers_count=user.followers_count,
    )
    session.add(user_info)

