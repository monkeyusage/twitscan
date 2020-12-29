import logging
from typing import List, Optional, Set

from tweepy.models import Status, User

from twitscan import api, config, session
from twitscan.errors import UserProtectedError
from twitscan.models import (
    Entourage,
    Hashtag,
    Interaction,
    Link,
    Mention,
    TwitscanStatus,
    TwitscanUser,
)


def check_status(raw_status: Status) -> Optional[TwitscanStatus]:
    """Check if status id is in database
    Return status if yes else return None
    """
    existing_status: Optional[TwitscanStatus] = (
        session.query(TwitscanStatus)
        .filter(TwitscanStatus.status_id == raw_status.id)
        .one_or_none()
    )
    if existing_status is not None:
        return existing_status
    return None


def save_status(raw_status: Status) -> TwitscanStatus:
    """Save the tweepy status in database if does not exist
    Add mentions in database if they exist
    Return it anyway
    """
    existing_status = check_status(raw_status)
    if existing_status is not None:
        return existing_status

    is_retweet: bool = True if hasattr(raw_status, "retweeted_status") else False
    text: str = (
        raw_status.full_text if hasattr(raw_status, "full_text") else raw_status.text
    )
    status: TwitscanStatus = TwitscanStatus(
        user_id=raw_status.user.id,
        text=text,
        status_id=raw_status.id,
        created_at=raw_status.created_at,
        favorite_count=raw_status.favorite_count,
        retweet_count=raw_status.retweet_count,
        in_reply_to_status_id=raw_status.in_reply_to_status_id,
        in_reply_to_user_id=raw_status.in_reply_to_user_id,
        is_retweet=is_retweet,
    )

    mentions: List[Mention] = [
        Mention(status_id=raw_status.id, user_id=user["id"])
        for user in raw_status.entities["user_mentions"]
    ]

    urls: List[Link] = [
        Link(status_id=raw_status.id, link=url["expanded_url"])
        for url in raw_status.entities["urls"]
    ]

    tags: List[Hashtag] = [
        Hashtag(status_id=raw_status.id, hashtag_name=hashtag["text"])
        for hashtag in raw_status.entities["hashtags"]
    ]

    session.add(status)
    session.add_all(mentions)
    session.add_all(urls)
    session.add_all(tags)

    session.commit()

    return status


def check_user(
    screen_name: Optional[str] = None, user_id: Optional[int] = None
) -> Optional[TwitscanUser]:
    """Checks if user is in database, if so returns it otherwise returns None"""
    if screen_name:
        user: Optional[TwitscanUser] = (
            session.query(TwitscanUser)
            .filter(TwitscanUser.screen_name == screen_name)
            .one_or_none()
        )
    else:
        user = (
            session.query(TwitscanUser)
            .filter(TwitscanUser.user_id == user_id)
            .one_or_none()
        )
    if user is not None:
        return user
    return None


def scan_twitter(user_id: Optional[int], screen_name: Optional[str]) -> TwitscanUser:
    """Fetches user from twitter, Saves it in db and queries db for user"""
    # fetch user from twitter
    raw_user: User = (
        api.get_user(screen_name=screen_name)
        if screen_name
        else api.get_user(user_id=user_id)
    )
    if raw_user.protected:
        raise UserProtectedError(f"User {raw_user.screen_name} is protected")
    return save_user(raw_user)  # add user to database


def scan(
    user_id: Optional[int] = None, screen_name: Optional[str] = None
) -> TwitscanUser:
    """Checks if user is already scanned
    if so : retrieves user from db
    else : scans user from twitter adds it to db and returns it
    """
    assert not (
        (user_id is None) and (screen_name is None)
    ), "Both identifiers for User are None"

    maybe_user: Optional[TwitscanUser] = check_user(
        user_id=user_id, screen_name=screen_name
    )
    if maybe_user is None:
        logging.debug(
            f"Scanning user : {screen_name if screen_name else user_id} from twitter"
        )
        db_user: TwitscanUser = scan_twitter(user_id=user_id, screen_name=screen_name)
        return db_user
    logging.debug(
        f"User {maybe_user.screen_name} already in database, scanning from db"
    )
    return maybe_user


def save_entourage(user: User) -> None:
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


def save_interactions(user: User) -> None:
    """Uses twitter api to get latest tweets and retweets / comments / likes
    Stores user's related interactions in database
    """
    logging.debug(f"Fetching tweets for {user.screen_name}")
    chirps: List[TwitscanStatus] = [
        save_status(st)
        for st in api.user_timeline(
            screen_name=user.screen_name,
            count=config["MAX_TWEETS"],
            include_rts=True,
            tweet_mode="extended",
        )
    ]

    logging.debug(f"Fetching favorites for {user.screen_name}")

    liked: Set[int] = set(
        [save_status(st).status_id for st in api.favorites(user.screen_name)]
    )

    retweeted: Set[int] = set([chirp.status_id for chirp in chirps if chirp.is_retweet])
    comments: Set[int] = set(
        [chirp.status_id for chirp in chirps if chirp.in_reply_to_status_id]
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


def save_user(user: User) -> TwitscanUser:
    """Uses Tweepy User to create and push user info to db"""
    logging.debug(f"Adding {user.screen_name} to database")
    twitscan_user: TwitscanUser = TwitscanUser(
        user_id=user.id,
        screen_name=user.screen_name,
        created_at=user.created_at,
        verified=user.verified,
        favorites_count=user.favourites_count,
        status_count=user.statuses_count,
        friends_count=user.friends_count,
        followers_count=user.followers_count,
    )
    session.add(twitscan_user)
    save_entourage(user)
    save_interactions(user)

    session.commit()

    full_user: Optional[TwitscanUser] = (
        session.query(TwitscanUser).filter(TwitscanUser.user_id == user.id).first()
    )
    assert (
        full_user is not None
    ), "Could not retrieve user from database after saving it"

    return full_user
