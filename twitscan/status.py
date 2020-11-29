from tweepy.models import RawStatus
from twitscan.models import Status, Mention
from twitscan import session
from typing import Optional, List

def exists(raw_status:RawStatus) -> bool:
    existing_status: Optional[Status] = (
            session.query(Status).filter(Status.status_id == raw_status.id).one_or_none()
    )
    if existing_status is not None:
        return True
    return False

def save_status(raw_status:RawStatus) -> None:
    if exists(raw_status):
        return
    status: Status = Status(
        user_id=raw_status.user_id,
        text=raw_status.text,
        status_id=raw_status.id,
        created_at=raw_status.created_at,
        favorite_count=raw_status.favorite_count,
        retweet_count=raw_status.retweet_count,
        in_reply_to_status_id=raw_status.in_reply_to_status_id,
        in_reply_to_user_id=raw_status.in_reply_to_user_id,
        is_retweet=raw_status.is_retweet,
    )

    mentions: List[Mention] = [
        Mention(status_id=raw_status.id, user_id=user_id)
        for user_id in raw_status.user_mentions
    ]
    session.add(status)
    session.add_all(mentions)
    session.add()
