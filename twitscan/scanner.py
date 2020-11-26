import logging
from os import stat
from typing import List, Set, Optional, Dict, Any
from datetime import datetime

from tqdm import tqdm
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

        self._save()

    def _save(self) -> None:
        # check if status exists
        existing_status: Optional[Status] = (
            session.query(Status).filter(Status.status_id == self.id).one_or_none()
        )
        if existing_status is not None:
            return

        # add  mentions and status
        self._add_mentions()
        self._add_status()

        session.commit()

    def _add_status(self) -> None:
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
        session.add(status)

    def _add_mentions(self) -> None:
        mentions: List[Mention] = [
            Mention(status_id=self.id, user_id=user_id)
            for user_id in self.user_mentions
        ]
        session.add_all(mentions)

    def __str__(self) -> str:
        return f"TwitterStatus(user_id={self.user_id}, id={self.id}, likes={self.favorite_count}, rts={self.retweet_count})"

    def __repr__(self) -> str:
        return str(self)


class TwitterUser:
    """Main interface for twitscan library
    Scans User if not already in database and pushes the latter to db
    Allows for easy analysis of user data
    """

    def __init__(
        self,
        user_id: Optional[int] = None,
        screen_name: Optional[str] = None,
        debug_mode: bool = False,
    ):
        assert not (
            (user_id is None) and (screen_name is None)
        ), "Both identifiers for User are None"

        if debug_mode:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

        self._user = TwitterUser._scan(user_id=user_id, screen_name=screen_name)
        self.screen_name = self._user.screen_name
        self.id = self._user.user_id

    @staticmethod
    def _scan(user_id: Optional[int], screen_name: Optional[str]) -> User:
        """Checks if user is already scanned, if so retrieves user else scans user from twitter"""
        user: Optional[User] = TwitterUser.check_user(
            user_id=user_id, screen_name=screen_name
        )
        if user is None:
            logging.info(
                f"Scanning user : {screen_name if screen_name else user_id} from twitter"
            )
            db_user: User = TwitterUser._scan_twitter(user_id=user_id, screen_name=screen_name)
            return db_user
        else:
            logging.info(
                f"User {user.screen_name} already in database, scanning from db"
            )
            return user

    @staticmethod
    def _scan_twitter(user_id: Optional[int], screen_name: Optional[str]) -> User:
        """Fetches user from twitter, Saves it in db and queries db for user"""
        # fetch user from twitter
        user: RawUser = (
            api.get_user(screen_name=screen_name)
            if screen_name
            else api.get_user(user_id=user_id)
        )
        TwitterUser._save(user)  # add user to database
        db_user: User = session.query(User).filter(
            User.user_id == user.id
        ).first()  # query User from database
        return db_user

    @staticmethod
    def check_user(
        screen_name: Optional[str] = None, user_id: Optional[int] = None
    ) -> Optional[User]:
        """Checks if user is in database, if so returns it otherwise returns None"""
        if screen_name:
            user: Optional[User] = (
                session.query(User)
                .filter(User.screen_name == screen_name)
                .one_or_none()
            )
        else:
            user = session.query(User).filter(User.user_id == user_id).one_or_none()
        if user is not None:
            return user
        return None

    @staticmethod
    def _add_user(user: RawUser) -> None:
        """Uses Tweepy User to create and push user info to db"""
        logging.debug(f"Adding {user.screen_name} to database")
        user_info: User = User(
            user_id=user.id,
            screen_name=user.screen_name,
            created_at=user.created_at,
            verified=user.verified,
            favorites_count=user.favourites_count,
            status_count=user.statuses_count,
            friends_count=user.friends_count,
            followers_count=user.followers_count,
        )
        session.add(user_info)

    @staticmethod
    def _add_entouage(user: RawUser) -> None:
        """Calls twitter api to get friends and followers
        Pushes those ids in user's entourage
        """
        logging.debug(f"Fetching friends (followees) for {user.screen_name}")
        friends: Set[int] = set(api.friends_ids(user.id))
        logging.debug(f"Fetching followers for {user.screen_name}")
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
    def _add_interactions(user: RawUser) -> None:
        """Uses twitter api to get latest tweets and retweets / comments / likes
        Stores user's related interactions in database
        """
        logging.debug(f"Fetching tweets for {user.screen_name}")
        chirps: List[TwitterStatus] = [
            TwitterStatus(status)
            for status in api.user_timeline(
                screen_name=user.screen_name,
                count=config["MAX_TWEETS"],
                include_rts=True,
                tweet_mode="extended",
            )
        ]

        logging.debug(f"Fetching favorites for {user.screen_name}")
        liked: Set[int] = set(
            [TwitterStatus(tweet).id for tweet in api.favorites(user.screen_name)]
        )

        retweeted: Set[int] = set([chirp.id for chirp in chirps if chirp.is_retweet])
        comments: Set[int] = set(
            [chirp.id for chirp in chirps if chirp.in_reply_to_status_id]
        )

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
    def _save(user: RawUser) -> None:
        """Uses tweepy User to add it into db aswell as its entourage and interactions"""
        logging.debug(f"Adding user related information to database")

        TwitterUser._add_user(user)
        TwitterUser._add_entouage(user)
        TwitterUser._add_interactions(user)

        session.commit()

    def get_stats(self) -> Dict[str, int]:
        """Retrieves basic stats from User database"""
        stats: Dict[str, Any] = {
            "n_tweets": len(self._user.chirps),
            "n_followers": self._user.followers_count,
            "n_friends": self._user.friends_count,
            "n_favorites": self._user.favorites_count,
            "n_retweets": len(
                list(filter(lambda inter: inter.retweet, self._user.interacted_tweets))
            ),
            "n_comments": len(
                list(filter(lambda inter: inter.comment, self._user.interacted_tweets))
            ),
        }
        return stats

    def get_friends(self, other_user: Optional[User] = None) -> Set[int]:
        user: User = self._user if other_user is None else other_user
        friends: Set[int] = set(
            map(
                lambda e: e.friend_follower_id,
                filter(lambda e: e.friend, user.entourage),
            )
        )
        return friends

    def get_followers(self, other_user: Optional[User] = None) -> Set[int]:
        user: User = self._user if other_user is None else other_user
        followers: Set[int] = set(
            map(
                lambda e: e.friend_follower_id,
                filter(lambda e: e.follower, user.entourage),
            )
        )
        return followers

    def get_entourage(self, other_user: Optional[User] = None) -> Set[int]:
        user: User = self._user if other_user is None else other_user
        entourage: Set[int] = set(map(lambda e: e.friend_follower_id, user.entourage))
        return entourage

    def get_common_entourage(self, other_user_id: int) -> Set[int]:
        """Retrieve user's entourage and others entourage and compare"""
        user_ff_ids: Set[int] = self.get_entourage()
        other_user: Optional[User] = TwitterUser.check_user(user_id=other_user_id)
        assert other_user is not None, "Other user not in database"
        other_ff_ids: Set[int] = self.get_entourage(other_user)
        return user_ff_ids & other_ff_ids

    def get_common_friends(self, other_user_id: int) -> Set[int]:
        """Retrieves user's friends and other's friends and compare"""
        user_friends_ids: Set[int] = self.get_friends()
        other_user: Optional[User] = TwitterUser.check_user(user_id=other_user_id)
        assert other_user is not None, "Other user not in database"
        other_friends_ids: Set[int] = self.get_friends(other_user)
        return user_friends_ids & other_friends_ids

    def get_common_followers(self, other_user_id: int) -> Set[int]:
        """Retrieves user's followers and other's followers and compare"""
        user_followers_ids: Set[int] = self.get_followers()
        other_followers_ids: Set[int] = set(
            session.query(Entourage.friend_follower_id)
            .filter(Entourage.user_id == other_user_id, Entourage.follower is True)
            .all()
        )
        return user_followers_ids & other_followers_ids

    def __str__(self) -> str:
        return f"TwitterUser({self.screen_name}, id={self.id})"

    def __repr__(self) -> str:
        return str(self)
