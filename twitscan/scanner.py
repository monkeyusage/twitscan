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
        user_id: int = None,
        screen_name: str = None,
        debug_mode: bool = False,
    ):
        if (not screen_name) and (not user_id):
            raise ValueError(
                "screen_name or user_id must be entered when creating a TwitterUser"
            )

        if user_id:
            user: RawUser = api.get_user(user_id=user_id)
        else:
            user = api.get_user(screen_name=screen_name)

        # basic user information
        self.screen_name: str = user.screen_name
        self.id: int = user.id
        self.created_at: datetime = user.created_at
        self.verified: bool = user.verified

        # utility attributes
        self.debug_mode: bool = debug_mode

        # given statistics for all users
        self.favorites_count: int = user.favourites_count
        self.statuses_count: int = user.statuses_count
        self.friends_count: int = user.friends_count
        self.followers_count: int = user.followers_count

        # information that requires api calls
        self.liked: List[TwitterStatus] = self.get_liked()
        self.chirps: List[TwitterStatus] = self.get_chirps()
        self.friends: List[int] = self.get_friends()
        self.followers: List[int] = self.get_followers()

        # compiling user info and dumping it in database
        self.save()

    def debug(self, msg: str) -> None:
        if self.debug_mode:
            print(msg)

    def get_liked(self) -> List[TwitterStatus]:
        self.debug(f"Fetching favorites for {self}")
        favorites = api.favorites(self.screen_name)
        favs: List[TwitterStatus] = [TwitterStatus(tweet) for tweet in favorites]
        return favs

    def get_chirps(self) -> List[TwitterStatus]:
        self.debug(f"Fetching tweets for {self}")
        if config["MAX_TWEETS"] <= 200:
            # if we set max tweets under or equal 200 we just throw one request
            chirps: List[RawStatus] = api.user_timeline(
                screen_name=self.screen_name,
                count=200,  # max allowed is 200
                include_rts=True,
                tweet_mode="extended",
            )
        else:
            # otherwise we throw requests until we get either all chirps or twitter limit being 3200
            chirps = []
            for older_tweets in Cursor(
                api.user_timeline,
                screen_name=self.screen_name,
                count=200,
                include_rts=True,
                tweet_mode="extended",
            ).pages():
                chirps.extend(older_tweets)
                if len(chirps) > config["MAX_TWEETS"]:
                    break
        filtered_tweets: List[TwitterStatus] = [
            TwitterStatus(status) for status in chirps
        ]
        return filtered_tweets

    def get_friends(self) -> List[int]:
        self.debug(f"Fetching friends (followees) for {self}")
        friends: List[int] = api.friends_ids(self.id)
        return friends

    def get_followers(self) -> List[int]:
        self.debug(f"Fetching followers for {self}")
        followers: List[int] = api.followers_ids(self.id)
        return followers

    def get_entourage(self) -> List[Entourage]:
        followers: Set[int] = set(self.followers)  # twitter ids
        friends: Set[int] = set(self.friends)  # twitter ids

        friends_followers = followers | friends
        persons: List[Entourage] = []
        for ff in friends_followers:
            is_friend = ff in friends
            is_follower = ff in followers
            person: Entourage = Entourage(
                user_id=self.id,
                friend_follower_id=ff,
                friend=is_friend,
                follower=is_follower,
            )
            persons.append(person)
        return persons

    def get_interactions(self) -> List[Interaction]:
        liked: Set[int] = set([like.id for like in self.liked])
        retweeted: Set[int] = set(
            [chirp.id for chirp in self.chirps if chirp.is_retweet]
        )
        comments: Set[int] = set(
            [chirp.id for chirp in self.chirps if chirp.in_reply_to_status_id]
        )

        statuses = liked | retweeted | comments
        interactions: List[Interaction] = []
        for status in statuses:
            is_like = status in liked
            is_retweet = status in retweeted
            is_comment = status in comments
            interaction = Interaction(
                user_id=self.id,
                status_id=status,
                like=is_like,
                retweet=is_retweet,
                comment=is_comment,
            )
            interactions.append(interaction)
        return interactions

    def _to_user(self) -> User:
        user_info: User = User(
            user_id=self.id,
            screen_name=self.screen_name,
            created_at=self.created_at,
            verified=self.verified,
            favorites_count=self.favorites_count,
            status_count=self.statuses_count,
            friends_count=self.friends_count,
            followers_count=self.followers_count,
        )
        return user_info

    def save(self) -> None:
        user_info = self._to_user()
        entourage = self.get_entourage()
        interactions = self.get_interactions()

        session.add(user_info)
        session.add_all(entourage)
        session.add_all(interactions)
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
