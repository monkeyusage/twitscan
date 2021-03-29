from __future__ import annotations

class EngagementScore:
    def __init__(
        self,
        user: int,
        target_user: int,
        common_friends: int,
        common_followers: int,
        likes_given: int,
        comments_given: int,
        retweets_given: int,
        mentions_given: int,
    ):
        self.user = user
        self.target_user = target_user
        self.common_friends = common_friends if common_friends else 0
        self.common_followers = common_followers if common_followers else 0
        self.likes_given = likes_given
        self.comments_given = comments_given
        self.retweets_given = retweets_given
        self.mentions_given = mentions_given
        self._score = None

    @property
    def score(self):
        if self._score is None:
            self._force()
        return self._score

    def _force(self) -> None:
        self._score = (
            self.comments_given
            + self.retweets_given
            + self.mentions_given
            + self.likes_given
            + self.common_followers
            + self.common_friends
        )

    @staticmethod
    def deserialize(json_data:dict[str,int]) -> EngagementScore:
        del json_data['score']
        return EngagementScore(**json_data)


    def serialize(self) -> dict[str, int]:
        attrs = [attr for attr in dir(self) if not attr.startswith('_')]
        return dict((attr, getattr(self, attr)) for attr in attrs if type(getattr(self, attr)) == int)

    def __repr__(self) -> str:
        if self._score is None:
            self._force()
        return f"EngagementScore({self.user} -> {self.target_user}: {self.score})"