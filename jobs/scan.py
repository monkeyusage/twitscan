import logging
from argparse import ArgumentParser
from typing import List, Set, Optional
import time
import os
import sys

from tqdm import tqdm
import tweepy

sys.path.append('../twitscan')
from twitscan.errors import UserProtectedError
from twitscan.models import TwitscanUser
from twitscan import scanner, query, sync_session

parser = ArgumentParser()
parser.add_argument(
    "-d", "--debug", action="store_true", default=False, help="run in debug mode"
)


def handle_user_scan(
    user_id: Optional[int] = None, name: Optional[str] = None
) -> Optional[TwitscanUser]:
    if all((type(obj) == None for obj in (user_id, name))):
        raise TypeError("User is neither string nor int")
    user = name if user_id is None else user_id
    retries = 0
    while retries < 2:
        try:
            twitter_user: TwitscanUser = scanner.scan(screen_name=name, user_id=user_id)
            return twitter_user
        except UserProtectedError:
            logging.debug(f"User {user} is protected")
            return None
        except tweepy.TweepError as err:
            logging.debug(f"Got tweepy error scanning {user}")
            logging.debug(f"\n\t{err}")
            logging.debug("Sleeping for 5 seconds then trying to resume")
            for _ in tqdm(
                range(5), desc="Got Tweepy Error, retrying after 5 seconds sleep"
            ):
                time.sleep(1)
            retries += 1
            cmd = "cls" if os.name == "nt" else "clear"
            os.system(cmd)
            retries += 1
        except KeyboardInterrupt:
            logging.info("KeyboardInterrupt, terminating all")
            sync_session.close()
            exit(0)
    return None


def main() -> None:
    args = parser.parse_args()
    level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=level)

    with open("data/users.txt", "r") as file:
        users = file.read().split("\n")

    for user in users:
        twitter_user: Optional[TwitscanUser] = handle_user_scan(name=user)
        if twitter_user is None:
            continue
        followers: List[int] = query.followers(twitter_user)
        scanned_ids: Set[int] = set(
            map(lambda user: user.user_id, query.all_users())
        )  # get all user ids
        follower_ids: List[int] = list(
            filter(lambda follower_id: follower_id not in scanned_ids, followers)
        )
        if len(follower_ids) >= 1600:
            logging.debug(
                f"Main user @{user} has more than allowed number of followers, skipping"
            )
            continue
        with tqdm(total=len(follower_ids), position=0, leave=True) as pbar:
            description = f"Scanning followers of main user {user}"
            for follower_id in tqdm(
                follower_ids, position=0, leave=True, desc=description
            ):
                handle_user_scan(user_id=follower_id)
                pbar.update()
