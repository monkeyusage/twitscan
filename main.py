import tweepy
from tweepy.models import User
from secret import auth
from typing import List, Dict, Union

api = tweepy.API(
    auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True
)


class TwitterUser:
    """A dummy interface to the tweepy wrapper"""

    def __init__(self, screen_name):
        self.user = api.get_user(screen_name=screen_name)
        self.tweets = self.get_tweets()

    def get_tweets(self) -> List[int]:
        tweets = api.user_timeline(
            screen_name=self.user.screen_name,
            count=200,  # max allowed is 200
            include_rts=False,
            tweet_mode="extended",
        )
        return tweets


class Follower(TwitterUser):
    """A simple class to collect data related to follower of Participant"""

    def __init__(self, screen_name: str, follows: TwitterUser, nretweets: int):
        super().__init__(screen_name)
        self.follows: TwitterUser = follows
        self.nlikes: int = self.get_nlikes()
        self.nretweets: int = nretweets
        self.comments: str = ""
        self.ncomments: int = 0
        self.scan_comments()

    def get_nlikes(self) -> int:
        favs = api.favorites(self.user.screen_name)
        liked_follows = list(
            filter(lambda tweet: tweet.user.id == self.follows.user.id, favs)
        )
        return len(liked_follows)

    def scan_comments(self) -> None:
        for tweet in self.tweets:
            if tweet.in_reply_to_screen_name == self.follows.user.screen_name:
                self.update_comments(tweet.full_text)

    def update_comments(self, comment: str) -> None:
        """Add a comment to comment list"""
        comment = comment.replace("\t", "").replace("\n", "") + " newline "
        self.comments += comment
        self.ncomments += 1

    def print_comments(self) -> None:
        comments = self.comments.split("newline")
        for comment in comments:
            print(f"{self.user.screen_name} : {comment.strip()}")

    def __repr__(self) -> str:
        return f"Follower({self.user.screen_name}, id={self.user.id})"

    def info(self) -> List[str]:
        info = [
            self.user.screen_name,
            str(self.user.id),
            str(self.nlikes),
            str(self.nretweets),
            str(self.ncomments),
            self.comments,
        ]
        return info


class Participant(TwitterUser):
    """Main interface to retrieve data, scans data from participant and his/her followers and saves it"""

    def __init__(self, screen_name: str):
        super().__init__(screen_name)
        self.followers = self.get_followers()

    def get_followers(self) -> List[Follower]:
        followers : List[User] = []
        for page in tweepy.Cursor(
            api.followers, screen_name=self.user.screen_name
        ).pages():
            if len(followers) > 500:
                return []
            followers.extend(page)
        
        retweeters = self.get_retweeters(followers)
        analysed_followers : List[Follower] = [
            Follower(
                screen_name=follower.screen_name,
                follows=self,
                nretweets=retweeters[follower.screen_name],
            )
            for follower in followers
            if not follower.protected
        ]
        return analysed_followers

    def get_retweeters(self, followers: List[User]) -> Dict[str, int]:
        """assigns a number of retweets for each follower
        Parsing for number of retweets is more efficient here than in each follower
        This allow for only one api call per tweet instead of parsing participant tweets by every follower
        """
        retweeters = {follower.screen_name: 0 for follower in followers}
        for tweet in self.tweets:
            retweets = api.retweets(tweet.id)
            for retweet in retweets:
                retweeters[retweet.user.screen_name] += 1
        return retweeters

    def save(self, name: str):
        """Saves data in tabular format
        participant_name | follower_name | follower_id | likes | retweets | ncomments | comments
        """
        header = [
            "participant_name",
            "ntweets",
            "follower_name",
            "follower_id",
            "likes",
            "retweets",
            "ncomments",
            "comments",
        ]
        with open("data/" + name + ".tsv", "w") as f:
            f.write("\t".join(header) + "\n")
            for follower in self.followers:
                f.write(
                    self.user.screen_name + "\t" + str(len(self.tweets)) +"\t" + "\t".join(follower.info()) + "\n"
                )

    def __repr__(self):
        return f"Participant({self.user.screen_name}, id={self.user.id})"


if __name__ == "__main__":
    p = Participant("RiotKael")
    p.save("RiotKael")
