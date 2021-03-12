import sys
import os
sys.path.append('../twistcan')
from twitscan import query

TEST_USERNAME = os.environ['TWITSCAN_TEST_USER']
TEST_USER = query.user_by_screen_name(TEST_USERNAME)
if TEST_USER is None:
    raise Exception('Could not retrieve test user from database')

def test_followers():
    followers = query.followers(TEST_USER)
    assert isinstance(followers, list), 'this should be a list'