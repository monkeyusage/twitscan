from typing import List, Literal, Set
from datetime import datetime
from sqlite3 import Connection

import tweepy
from tqdm import tqdm
from tweepy.models import User
from tweepy.models import Status as RawStatus

from secret import auth

api = tweepy.API(
    auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True
)


class Status:
    """Acts like a filter for useful information when retrieving tweepy Statuses"""

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
        self.is_retweet: bool = self.text.startswith("RT ")
        self.user_mentions: List[int] = [
            user["id"] for user in twitter_status.entities["user_mentions"]
        ]

    def __str__(self) -> str:
        return f"Status(user_id={self.user_id}, id={self.id}, likes={self.favorite_count}, rts={self.retweet_count})"

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

    MAX_TWEETS: Literal[500] = 500
    if MAX_TWEETS > 3200:
        raise ValueError(
            "Twitter API accepts retrieval of maximum 3200 tweets for each user"
        )

    def __init__(
        self, screen_name: str, db_connection: Connection, debug_mode: bool = False
    ):
        if not screen_name:
            raise ValueError("Screen name must be entered when creating a Twitter User")

        user: User = api.get_user(screen_name=screen_name)

        # basic attributes
        self.screen_name: str = user.screen_name
        self.id: int = user.id
        self.created_at: datetime = user.created_at
        self.verified: bool = user.verified

        # utility attributes
        self.debug_mode: bool = debug_mode
        self.connection: Connection = db_connection

        # advanced attributes for all users
        self.favorites_count: int = user.favourites_count
        self.liked: List[Status] = self.get_liked()

        self.statuses_count: int = user.statuses_count
        self.tweets: List[Status] = self.get_tweets()
        self.retweets_of_user: List[Status] = self.get_retweets()

        self.friends_count: int = user.friends_count
        self.friends: Set[int] = self.get_friends()

        self.followers_count: int = user.followers_count

    def debug(self, msg: str) -> None:
        if self.debug_mode:
            print(msg)

    def get_liked(self) -> List[Status]:
        self.debug(f"Getting favorites for {self}")
        favs: List[Status] = [
            Status(tweet) for tweet in api.favorites(self.screen_name)
        ]
        return favs

    def get_tweets(self) -> List[Status]:
        self.debug(f"Getting tweets for {self}")
        if TwitterUser.MAX_TWEETS <= 200:
            # if we set max tweets under or equal 200 we just throw one request
            tweets: List[RawStatus] = api.user_timeline(
                screen_name=self.screen_name,
                count=200,  # max allowed is 200
                include_rts=False,
                tweet_mode="extended",
            )
        else:
            # otherwise we throw requests until we get either all tweets or twitter limit being 3200
            tweets = []
            for older_tweets in tweepy.Cursor(
                api.user_timeline,
                screen_name=self.screen_name,
                count=200,
                include_rts=False,
                tweet_mode="extended",
            ).pages():
                tweets.extend(older_tweets)
                if len(tweets) > TwitterUser.MAX_TWEETS:
                    break
        filtered_tweets: List[Status] = [Status(status) for status in tweets]
        return filtered_tweets

    def get_retweets(self) -> List[Status]:
        retweets: List[Status] = []
        for tweet in self.tweets:
            rts = [Status(rt) for rt in api.retweets(tweet.id)]
            retweets.extend(rts)
        return retweets

    def get_friends(self) -> Set[int]:
        self.debug(f"Getting friends (followees) for {self}")
        friends: List[int] = api.friends_ids(self.id)
        return set(friends)

    def __str__(self) -> str:
        return f"TwitterUser({self.screen_name}, id={self.id})"

    def __repr__(self) -> str:
        return str(self)


class UserScanner(TwitterUser):
    MAX_FOLLOWERS: Literal[100] = 100
    """Main interface to retrieve data, scans data from participant and his/her followers and saves it"""

    def __init__(
        self, screen_name: str, db_connection: Connection, debug_mode: bool = False
    ):
        super().__init__(screen_name, db_connection, debug_mode)
        if self.followers_count > UserScanner.MAX_FOLLOWERS:
            raise ValueError(
                f"{self} has more than maximum number of followers allowed for this study: {UserScanner.MAX_FOLLOWERS}"
            )
        self.followers: List[User] = self.get_followers()

    def get_followers(self) -> List[User]:
        """parses followers information and stores in Follower attributes"""
        followers: List[User] = []
        self.debug(f"Getting followers for {self}")
        for page in tweepy.Cursor(api.followers, screen_name=self.screen_name).pages():
            followers.extend(page)

        self.debug(f"\n####################\Scanning followers for {self}")
        registered_followers: List[TwitterUser] = [
            TwitterUser(
                screen_name=follower.screen_name,
                db_connection=self.connection,
                debug_mode=self.debug_mode,
            )
            for follower in tqdm(followers)
            if not follower.protected
        ]
        return registered_followers

    def __repr__(self):
        return f"UserScanner({self.screen_name}, id={self.id})"
