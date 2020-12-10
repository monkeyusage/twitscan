import logging
from argparse import ArgumentParser
from typing import List

from tqdm import tqdm

from twitscan.errors import UserProtectedError
from twitscan.models import TwitscanUser
from twitscan.user import scan, get_followers

parser = ArgumentParser()
parser.add_argument(
    "-d", "--debug", action="store_true", default=False, help="run in debug mode"
)

if __name__ == "__main__":
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    with open("data/users.txt", "r") as file:
        users = file.read().split("\n")

    for user in users:
        try:
            twitter_user: TwitscanUser = scan(screen_name=user)
        except UserProtectedError:
            print(f"Main user {user} is protected")
            continue
        followers: List[int] = get_followers(twitter_user)
        for follower_id in tqdm(followers):
            try:
                scan(user_id=follower_id)
            except UserProtectedError as err:
                print(err)
