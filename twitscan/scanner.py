from twitscan.errors import TwitscanError
from typing import List, Literal, Set
from datetime import datetime

from tqdm import tqdm
from tweepy import Cursor
from tweepy.models import User as RawUser
from tweepy.models import Status as RawStatus

from twitscan import api, session
from twitscan.models import Entourage, Status, Mention
from twitscan.models import interacted_status as Interaction


class TwitterStatus:
    """
    Acts like a filter for useful information when retrieving tweepy Statuses
    Inserts Status and related information into database
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

        mentions: List[Mention] = [
            Mention(status_id=self.id, user_id=user_id)
            for user_id in self.user_mentions
        ]
        session.add_all(mentions)

        status: Status = Status(
            status_id=self.id,
            created_at=self.created_at,
            favorite_count=self.favorite_count,
            retweet_count=self.retweet_count,
            in_reply_to_status_id=self.in_reply_to_screen_name,
            in_reply_to_user_id=self.in_reply_to_user_id,
            is_retweet=self.is_retweet,
        )
        session.add(status)
        session.commit()

    def __str__(self) -> str:
        return f"TwitterStatus(user_id={self.user_id}, id={self.id}, likes={self.favorite_count}, rts={self.retweet_count})"

    def __repr__(self) -> str:
        return str(self)


class TwitterUser:
    """A dummy interface to the tweepy wrapper
    Stores user information as well as:
        debug mode
        favorites
        tweets
        friends (users followed)
    """

    MAX_TWEETS: Literal[300] = 300
    if MAX_TWEETS > 3200:
        raise ValueError(
            "Twitter API accepts retrieval of maximum 3200 tweets for each user"
        )

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

        # basic attributes
        self.screen_name: str = user.screen_name
        self.id: int = user.id
        self.created_at: datetime = user.created_at
        self.verified: bool = user.verified

        # utility attributes
        self.debug_mode: bool = debug_mode

        # advanced attributes for all users
        self.favorites_count: int = user.favourites_count
        self.liked: List[TwitterStatus] = self.get_liked()

        self.statuses_count: int = user.statuses_count
        self.chirps: List[TwitterStatus] = self.get_tweets()
        self.retweets_of_user: List[TwitterStatus] = self.get_retweets()

        self.friends_count: int = user.friends_count
        self.friends: List[int] = self.get_friends()

        self.followers_count: int = user.followers_count
        self.followers: List[int] = self.get_followers()

        entourage = self.get_entourage()
        session.add_all(entourage)

        session.commit()

    def debug(self, msg: str) -> None:
        if self.debug_mode:
            print(msg)

    def get_liked(self) -> List[TwitterStatus]:
        self.debug(f"Getting favorites for {self}")
        favorites = api.favorites(self.screen_name)
        favs: List[TwitterStatus] = [TwitterStatus(tweet) for tweet in favorites]
        return favs

    def get_chirps(self) -> List[TwitterStatus]:
        self.debug(f"Getting tweets for {self}")
        if TwitterUser.MAX_TWEETS <= 200:
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
                if len(chirps) > TwitterUser.MAX_TWEETS:
                    break
        filtered_tweets: List[TwitterStatus] = [
            TwitterStatus(status) for status in chirps
        ]
        return filtered_tweets

    def get_friends(self) -> List[int]:
        self.debug(f"Getting friends (followees) for {self}")
        friends: List[int] = api.friends_ids(self.id)
        return friends

    def get_followers(self) -> List[int]:
        followers: List[int] = []
        self.debug(f"Getting followers for {self}")
        for page in Cursor(api.followers, screen_name=self.screen_name).pages():
            ids = [user.id for user in page]
            followers.extend(ids)
        return followers

    def get_entourage(self) -> List[Entourage]:
        followers : Set[int] = set(self.followers) # twitter ids
        friends : Set[int] = set(self.friends) # twitter ids
        both  = followers & friends
        all_entourage = followers | friends        
        entourage : List[Entourage] = []
        for e in all_entourage:
            if e in both:
                entourage.append(Entourage(user_id=self.id, entourage_id=e, friend=True, follower=True))
            elif e in followers:
                entourage.append(Entourage(user_id=self.id, entourage_id=e, friend=False, follower=True))
            else:
                entourage.append(Entourage(user_id=self.id, entourage_id=e, friend=True, follower=False))
        return entourage

    def get_interaction(self) -> List[Interaction]:
        liked = self.liked
        retweeted = [chirp for chirp in self.chirps if chirp.is_retweet] 
        comments = [chirp for chirp in self.chrips if chirp.in_reply_to_status_id]
        
        return

    def __str__(self) -> str:
        return f"TwitterUser({self.screen_name}, id={self.id})"

    def __repr__(self) -> str:
        return str(self)


class UserScanner(TwitterUser):
    MAX_FOLLOWERS: Literal[100] = 100
    """Main interface to retrieve data, scans data from participant and his/her followers and saves it"""

    def __init__(self, screen_name: str, debug_mode: bool = False):
        super().__init__(screen_name=screen_name, debug_mode=debug_mode)
        if self.followers_count > UserScanner.MAX_FOLLOWERS:
            raise TwitscanError(
                f"{self} has more than maximum number of followers allowed for this study: {UserScanner.MAX_FOLLOWERS}",
                "Either raise the maximum allowed number of followers or remove the user from the scanning list",
            )
        self.user_followers: List[TwitterUser] = self.scan_followers()

    def scan_followers(self) -> List[TwitterUser]:
        """parses followers information and stores in Follower attributes"""
        self.debug(f"\n####################\nScanning followers for {self}")
        user_followers: List[TwitterUser] = [
            TwitterUser(
                user_id=follower_id,
                debug_mode=self.debug_mode,
            )
            for follower_id in tqdm(self.followers)
            if not api.get_user(follower_id).protected
        ]
        return user_followers

    def __repr__(self):
        return f"UserScanner({self.screen_name}, id={self.id})"
