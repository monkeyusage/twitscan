from twitscan import session
from twitscan.models import User, Status, Friend, Mention


def add_user(user) -> None:
    session
    return


def add_status(status) -> None:
    mentions = status.user_mentions
    new_mentions = [
        Mention(status_id=status.id, user_id=user_id) for user_id in mentions
    ]

    for mention in new_mentions:
        session.add(mention)

    new_status: Status = Status(
        status_id=status.id,
        text=status.text,
        created_at=status.created_at,
        favorite_count=status.favorites_count,
        retweet_count=status.retweet_count,
        in_reply_to_status_id=status.in_reply_to_status_id,
        in_reply_to_user_id=status.in_reply_to_user_id,
        is_retweet=status.is_retweet,
        user_id=status.user_id,
        user_mentions=new_mentions,
    )
    session.add(new_status)
    session.commit()


if __name__ == "__main__":
    from twitscan.scanner import TwitterStatus

    TwitterStatus()
