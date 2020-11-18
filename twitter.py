from typing import Dict, Iterable, List, Literal, Set
from datetime import datetime

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

    def __init__(self, screen_name: str, debug_mode: bool = False):
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

        # advanced attributes for all users
        self.favorites_count: int = user.favourites_count
        self.liked: List[Status] = self.get_liked()

        self.statuses_count: int = user.statuses_count
        self.tweets: List[Status] = self.get_tweets()

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

    def get_friends(self) -> Set[int]:
        self.debug(f"Getting friends (followees) for {self}")
        friends: List[int] = api.friends_ids(self.id)
        return set(friends)

    def __str__(self) -> str:
        return f"TwitterUser({self.screen_name}, id={self.id})"

    def __repr__(self) -> str:
        return str(self)


class Follower(TwitterUser):
    """A simple class to collect data related to follower of Participant"""

    def __init__(
        self,
        screen_name: str,
        follows: TwitterUser,
        retweets: List[Status],
        debug_mode: bool = False,
    ):
        super().__init__(screen_name, debug_mode)
        self.follows: TwitterUser = follows
        self.retweets: List[Status] = retweets

    def __repr__(self) -> str:
        return f"Follower({self.screen_name}, id={self.id})"


class Participant(TwitterUser):
    MAX_FOLLOWERS: Literal[100] = 100
    """Main interface to retrieve data, scans data from participant and his/her followers and saves it"""

    def __init__(self, screen_name: str, debug_mode: bool = False):
        super().__init__(screen_name, debug_mode)
        if self.followers_count > Participant.MAX_FOLLOWERS:
            raise ValueError(
                f"{self} has more than maximum number of followers allowed for this study: {Participant.MAX_FOLLOWERS}"
            )
        self.followers: List[Follower] = self.get_followers()

    def get_followers(self) -> List[Follower]:
        """parses followers information and stores in Follower attributes"""
        followers: List[User] = []
        self.debug(f"Getting followers for {self}")
        for page in tweepy.Cursor(api.followers, screen_name=self.screen_name).pages():
            followers.extend(page)

        self.debug(f"Getting retweets for {self}")
        retweeters: Dict[int, List[Status]] = self.get_retweeters(followers)
        self.debug(f"\n####################\Scanning followers for {self}")
        analysed_followers: List[Follower] = [
            Follower(
                screen_name=follower.screen_name,
                follows=self,
                retweets=retweeters[follower.id],
                debug_mode=self.debug_mode,
            )
            for follower in tqdm(followers)
            if not follower.protected
        ]
        return analysed_followers

    def get_retweeters(self, followers: List[User]) -> Dict[int, List[Status]]:
        """assigns tweets from Participant rt'ed by follower for each follower
        Parsing for retweets is more efficient here than in each follower
        This allow for only one api call per tweet instead of parsing participant tweets by every follower
        :param followers: List[User] list of raw  followers
        :returns: Dict[str, List[Status]]: dict storing (screen_name, list of tweets the followers rt'ed)
        """
        follower_id_set: Set[int] = set(follower.id for follower in followers)
        # for each follower we create an empty list of tweets and fill those with tweets they have rt'ed
        retweeters: Dict[int, List[Status]] = {
            follower.id: [] for follower in followers
        }
        for tweet in self.tweets:
            # for every tweet we get all the associated retweets
            retweets: List[Status] = [
                Status(retweet) for retweet in api.retweets(tweet.id)
            ]
            # make sure the retweets we loop over come from our unprotected followers
            filtered: Iterable[Status] = filter(
                lambda retweet: retweet.user_id in follower_id_set,
                retweets,
            )
            # for each rt we append the original tweet to the follower who rt'ed it
            for retweet in filtered:
                retweeters[retweet.user_id].append(tweet)
        return retweeters

    def __repr__(self):
        return f"Participant({self.screen_name}, id={self.id})"
