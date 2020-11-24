import unittest
from twitscan import test_session, api
from twitscan.scanner import *
from twitscan.models import *
from tweepy.models import Status as RawStatus

status: RawStatus = api.user_timeline("nytimes", count=1)[0]
filtered: TwitterStatus = TwitterStatus(status)

print(filtered)


class db_tests(unittest.TestCase):
    def setUp(self) -> None:

        return
