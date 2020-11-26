from twitscan.errors import TooManyFollowersError
from typing import Callable, List, Set, Optional, Union
from datetime import datetime

from tqdm import tqdm
from tweepy import Cursor
from tweepy.models import User as RawUser
from tweepy.models import Status as RawStatus

from twitscan import api, session, config
from twitscan.models import Entourage, Status, Mention, Interaction, User


class TwitterStatus:
    """Filter for tweepy Statuses
    Inserts information into database
    """

    def __init__(self, twitter_status: RawStatus):
        self.user_id: int = twitter_status.user.id
        self.text: str = getattr(
            twitter_status, "full_text", getattr(twitter_status, "text", "")
        )
        self.id: int = twitter_status.id
        self.created_at: datetime = twitter_status.created_at
        self.favorite_count: int = twitter_status.favorite_count
        self.retweet_count: int = twitter_status.retweet_count
        self.in_reply_to_screen_name: str = twitter_status.in_reply_to_screen_name
        self.in_reply_to_status_id: int = twitter_status.in_reply_to_status_id
        self.in_reply_to_user_id: int = twitter_status.in_reply_to_user_id
        self.is_retweet: bool = hasattr(twitter_status, "retweeted_status")
        self.user_mentions: List[int] = [
            user["id"] for user in twitter_status.entities["user_mentions"]
        ]

        self.save()

    def save(self) -> None:
        # check if status exists
        existing_status: Optional[Status] = (
            session.query(Status).filter(Status.status_id == self.id).one_or_none()
        )
        if existing_status is not None:
            return

        # if not exists add  mentions and status
        mentions: List[Mention] = self.to_mentions()
        status: Status = self.to_status()

        session.add_all(mentions)
        session.add(status)
        session.commit()

    def to_status(self) -> Status:
        status: Status = Status(
            user_id=self.user_id,
            text=self.text,
            status_id=self.id,
            created_at=self.created_at,
            favorite_count=self.favorite_count,
            retweet_count=self.retweet_count,
            in_reply_to_status_id=self.in_reply_to_status_id,
            in_reply_to_user_id=self.in_reply_to_user_id,
            is_retweet=self.is_retweet,
        )
        return status

    def to_mentions(self) -> List[Mention]:
        mentions: List[Mention] = [
            Mention(status_id=self.id, user_id=user_id)
            for user_id in self.user_mentions
        ]
        return mentions

    def __str__(self) -> str:
        return f"TwitterStatus(user_id={self.user_id}, id={self.id}, likes={self.favorite_count}, rts={self.retweet_count})"

    def __repr__(self) -> str:
        return str(self)


class TwitterUser:
    """Filter for tweepy User class, adds information with api calls related to
    user.followers, user.friends, user.chrips (tweets or retweets), user interactions
    Stores all these records in database
    """

    def __init__(
        self,
        user_id: Optional[int] = None,
        screen_name: Optional[str] = None,
        debug_mode: bool = False,
    ):
        if (not screen_name) and (not user_id):
            raise ValueError(
                "screen_name or user_id must be entered when creating a TwitterUser"
            )

        self.debug_mode: bool = debug_mode

        if user := self.is_already_scanned(user_id=user_id, screen_name=screen_name, debug_mode=debug_mode) is not None:
            self.scan()

        self.screen_name = user.screen_name

    def debug(self, msg: str) -> None:
        if self.debug_mode:
            print(msg)

    def scan(self, user_id:Optional[int], screen_name:Optional[str]) -> None:
        # fetch user from twitter
        if user_id:
            user: RawUser = api.get_user(user_id=user_id)
        else:
            user = api.get_user(screen_name=screen_name)
        # requesting and compiling user info from tweeter then dumping it in database
        TwitterUser._save(user)

    @staticmethod
    def _add_user(user:RawUser) -> None:
        user_info: User = User(
            user_id=user.id,
            screen_name=user.screen_name,
            created_at=user.created_at,
            verified=user.verified,
            favorites_count=user.favorites_count,
            status_count=user.statuses_count,
            friends_count=user.friends_count,
            followers_count=user.followers_count,
        )
        session.add(user_info)

    @staticmethod
    def _add_entouage(user) -> None:
        print(f"Fetching friends (followees) for {user.screen_name}")
        friends: Set[int] = set(api.friends_ids(user.id))
        print(f"Fetching followers for {user.screen_name}")
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

    @staticmethod
    def _add_interactions(user:RawUser) -> None:
        print(f"Fetching tweets for {user.screen_name}")
        chirps : List[TwitterStatus] = [TwitterStatus(status) for status in api.user_timeline(screen_name=user.screen_name, count=config["MAX_TWEETS"],  include_rts=True,tweet_mode="extended",)]

        print(f"Fetching favorites for {user.screen_name}")
        liked : Set[int] = set([TwitterStatus(tweet).id for tweet in api.favorites(user.screen_name)])


        retweeted: Set[int] = set([chirp.id for chirp in chirps if chirp.is_retweet])
        comments: Set[int] = set([chirp.id for chirp in chirps if chirp.in_reply_to_status_id])

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

    @staticmethod
    def _save(user:RawUser) -> None:
        TwitterUser._add_user(user)
        TwitterUser._add_entouage(user)
        TwitterUser._add_interactions(user)

        session.commit()

    def __str__(self) -> str:
        return f"TwitterUser({self.screen_name}, id={self.id})"

    def __repr__(self) -> str:
        return str(self)

    def is_already_scanned(
        screen_name: Optional[str] = None, user_id: Optional[int] = None
    ) -> Optional[User]:
        """If user is in database we don't want to waste our api calls on him/her
        However if the user is being scanned we still want to scan the followers
        """
        if (screen_name is None) and (user_id is None):
            raise ValueError("Cannot query user, not screen_name or user_id given")
        if screen_name:
            user: Optional[User] = (
                session.query(User).filter(User.screen_name == screen_name).one_or_none()
            )
        else:
            user = session.query(User).filter(User.user_id == user_id).one_or_none()
        if user is not None:
            return user
        return None


def scan(user_name: str, debug_mode: bool = False) -> User:
    maybe_user: Optional[User] = is_already_scanned(user_name)
    if maybe_user is not None:
        print(f"Main user {user_name} already in database, fetching for its followers")
        followers: List[int] = list(
            map(
                lambda e: e.friend_follower_id,
                filter(lambda e: e.follower, maybe_user.entourage),
            )
        )
        user_id: int = maybe_user.user_id
    else:
        print(f"Scanning main user {user_name}")
        scanned_user: TwitterUser = TwitterUser(
            screen_name=user_name, debug_mode=debug_mode
        )
        followers = scanned_user.followers
        user_id = scanned_user.id

    user: User = session.query(User).filter(User.user_id == user_id)

    if len(followers) > config["MAX_FOLLOWERS"]:
        raise TooManyFollowersError(
            f"Main user {user_name} has too many followers for scannings"
        )

    is_protected: Callable[[int], bool] = lambda user_id: api.get_user(
        user_id=user_id
    ).protected

    for follower_id in tqdm(followers):
        if is_already_scanned(user_id=follower_id) or is_protected(follower_id):
            print(f"User {follower_id} already in database or protected")
            continue
        TwitterUser(user_id=follower_id, debug_mode=debug_mode)

    return user
