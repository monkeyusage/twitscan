from __future__ import annotations
import logging
from argparse import ArgumentParser
import time
import os
import sys

from tqdm import tqdm
from tweepy import TweepError

sys.path.append("../twitscan")
from twitscan.errors import UserProtectedError
from twitscan.models import Entourage, TwitscanUser
from twitscan import scanner, session


def handle_user_scan(
    user_id: int | None = None, name: str | None = None
) -> TwitscanUser | None:
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
        except TweepError as err:
            logging.debug(f"Got tweepy error scanning {user}")
            logging.debug(f"\n\t{err}")
            logging.debug("Sleeping for 5 seconds then trying to resume")
            time.sleep(5)
            retries += 1
            cmd = "cls" if os.name == "nt" else "clear"
            os.system(cmd)
            retries += 1
        except KeyboardInterrupt:
            logging.info("KeyboardInterrupt, terminating all")
            exit(1)
    return None


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument(
        "-d", "--debug", action="store_true", default=False, help="run in debug mode"
    )

    args = parser.parse_args()
    level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=level)

    with open("data/users.txt", "r") as file:
        users = file.read().split("\n")

    scanned_ids = set(map(lambda user: user.user_id, session.query(TwitscanUser).all()))
    for user in users:
        print(f"Scanning main user {user}")
        twitter_user: TwitscanUser | None = handle_user_scan(name=user)
        if twitter_user is None:
            print(f"Did not find main user {user} in DB")
            continue
        followers: list[Entourage] = list(
            filter(
                lambda ent: ent.follower and ent.friend_follower_id not in scanned_ids,
                twitter_user.entourage,
            )
        )

        if len(followers) >= 1600:
            logging.debug(
                f"Main user @{user} has more than allowed number of followers, skipping"
            )
            continue
        for follower in tqdm(followers):
            uid = follower.friend_follower_id
            print(f"Scanning follower: {uid}")
            handle_user_scan(user_id=uid)
            scanned_ids.add(uid)
