from typing import List, Optional

from tweepy.models import Status

from twitscan import session
from twitscan.models import Mention, Hashtag, Link, TwitscanStatus


def _exists(raw_status: Status) -> Optional[TwitscanStatus]:
    """Check if status id is in database
    Return True if yes else return False
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
    existing_status = _exists(raw_status)
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

    return status
