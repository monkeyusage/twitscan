from typing import Dict, Iterable, List, Literal, Set
import logging

import tweepy
from tqdm import tqdm
from tweepy.models import Status, User

from secret import auth

api = tweepy.API(
    auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True
)


class TwitterUser:
    """A dummy interface to the tweepy wrapper
    Stores user information as well as:
        debug mode
        favorites
        tweets
        friends (users followed)
    """

    def __init__(self, screen_name: str, debug: bool = False):
        if not screen_name:
            raise ValueError("Screen name must be entered when creating a Twitter User")
        
        self.user: User = api.get_user(screen_name=screen_name)

        # utility attributes
        self.debug = print if debug else lambda msg:None

        # common attributes for all users
        self.favs: List[Status] = self.get_favs()
        self.tweets: List[Status] = self.get_tweets()
        self.friends: Set[int] = self.get_friends()

    def get_favs(self) -> List[Status]:
        self.debug(f"Getting favorites for {str(self)}")
        favs: List[Status] = api.favorites(self.user.screen_name)
        return favs

    def get_tweets(self) -> List[Status]:
        self.debug(f"Getting tweets for {str(self)}")
        tweets: List[Status] = api.user_timeline(
            screen_name=self.user.screen_name,
            count=200,  # max allowed is 200
            include_rts=False,
            tweet_mode="extended",
        )
        return tweets

    def get_friends(self) -> Set[int]:
        self.debug(f"Getting friends (followees) for {str(self)}")
        friends: List[int] = api.friends_ids(self.user.id)
        return set(friends)

    def __str__(self) -> str:
        return f"TwitterUser({self.user.screen_name}, id={self.user.id})"

    def __repr__(self) -> str:
        return str(self)


class Follower(TwitterUser):
    """A simple class to collect data related to follower of Participant"""

    def __init__(
        self,
        screen_name: str,
        follows: TwitterUser,
        retweets: List[Status],
        debug: bool = False,
    ):
        super().__init__(screen_name, debug)
        self.follows: TwitterUser = follows
        self.retweets: List[Status] = retweets
        self.comments: List[Status] = self.get_comments()

    def get_comments(self) -> List[Status]:
        self.debug(f"\tRetrieving comments for {str(self)}")
        comments: List[Status] = [
            tweet
            for tweet in self.tweets
            if tweet.in_reply_to_screen_name == self.follows.user.screen_name
        ]
        return comments

    def count_likes(self) -> int:
        self.debug(f"\tCounting likes for {str(self)}")
        liked_follows = list(
            filter(lambda tweet: tweet.user.id == self.follows.user.id, self.favs)
        )
        return len(liked_follows)

    def __repr__(self) -> str:
        return f"Follower({self.user.screen_name}, id={self.user.id})"


class Participant(TwitterUser):
    MAX: Literal[100] = 100
    """Main interface to retrieve data, scans data from participant and his/her followers and saves it"""

    def __init__(self, screen_name: str, debug: bool = False):
        super().__init__(screen_name, debug)
        self.followers: List[Follower] = self.get_followers()

    def get_followers(self) -> List[Follower]:
        """parses followers information and stores in Follower attributes
        Filters
        """
        followers: List[User] = []
        self.debug(f"Getting followers for {str(self)}")
        for page in tweepy.Cursor(
            api.followers, screen_name=self.user.screen_name
        ).pages():
            if len(followers) > self.MAX:
                raise ValueError(
                    f"Participant has more than maximum number of followers allowed for this study: {self.MAX}"
                )
            followers.extend(page)

        self.debug(f"Getting retweets for {str(self)}")
        retweeters: Dict[str, List[Status]] = self.get_retweeters(followers)
        self.debug(f"Analysing followers for {str(self)}")
        analysed_followers: List[Follower] = [
            Follower(
                screen_name=follower.screen_name,
                follows=self,
                retweets=retweeters[follower.screen_name],
                debug=self.debug
            )
            for follower in tqdm(followers)
            if not follower.protected
        ]
        return analysed_followers

    def get_retweeters(self, followers: List[User]) -> Dict[str, List[Status]]:
        """assigns tweets from Participant rt'ed by follower for each follower
        Parsing for retweets is more efficient here than in each follower
        This allow for only one api call per tweet instead of parsing participant tweets by every follower
        :param followers: List[User] list of raw  followers
        :returns: Dict[str, List[Status]]: dict storing (screen_name, list of tweets the followers rt'ed)
        """
        follower_id_set: Set[int] = set(follower.id for follower in followers)
        # for each follower we create an empty list of tweets and fill those with tweets they have rt'ed
        retweeters: Dict[str, List[Status]] = {
            follower.screen_name: [] for follower in followers
        }
        for tweet in self.tweets:
            retweets: List[Status] = api.retweets(tweet.id)
            # make sure the retweets we loop over come from our unprotected followers
            retweets: Iterable[Status] = filter(
                lambda retweet: (retweet.user.id in follower_id_set)
                and (not retweet.user.protected),
                retweets,
            )
            # for each rt we append the original tweet to the follower who rt'ed it
            for retweet in retweets:
                retweeters[retweet.user.screen_name].append(tweet)
        return retweeters

    def __repr__(self):
        return f"Participant({self.user.screen_name}, id={self.user.id})"
