import logging
from argparse import ArgumentParser
from typing import List

from tqdm import tqdm

from twitscan.errors import UserProtectedError
from twitscan.models import TwitscanUser
from twitscan import scanner, query, session

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
            twitter_user: TwitscanUser = scanner.scan(screen_name=user)
        except UserProtectedError:
            print(f"Main user {user} is protected")
            continue
        followers: List[int] = query.followers(twitter_user)
        for follower_id in tqdm(followers):
            try:
                scanner.scan(user_id=follower_id)
            except UserProtectedError as err:
                print(err)
            except KeyboardInterrupt:
                session.close()
