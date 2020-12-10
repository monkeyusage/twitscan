import logging
from argparse import ArgumentParser
from typing import List, Set
import time

from tqdm import tqdm
import tweepy

from twitscan.errors import UserProtectedError
from twitscan.models import TwitscanUser
from twitscan import scanner, query, session

parser = ArgumentParser()
parser.add_argument(
    "-d", "--debug", action="store_true", default=False, help="run in debug mode"
)


def main() -> None:
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    with open("data/users.txt", "r") as file:
        users = file.read().split("\n")

    for user in users:
        try:
            twitter_user: TwitscanUser = scanner.scan(
                screen_name=user
            )  # scan main user
        except UserProtectedError:
            logging.info(f"Main user @{user} is protected")
            continue
        except KeyboardInterrupt:
            session.close()
            exit()
        followers: List[int] = query.followers(
            twitter_user
        )  # get followers for given user
        # remove followers that have already been scanned
        all_ids: Set[int] = set(
            map(lambda user: user.user_id, query.all_users())
        )  # get all user ids
        followers_scan: List[int] = list(
            filter(lambda follower_id: follower_id not in all_ids, followers)
        )
        if len(followers_scan) >= 1600:
            logging.info(
                f"Main user @{user} has more than allowed number of followers, skipping"
            )
            continue
        for follower_id in tqdm(followers_scan):
            retries = 0
            while retries < 5:
                try:
                    scanner.scan(user_id=follower_id)
                    break
                except tweepy.TweepError as err:
                    logging.info(f"Caught error:\n\t{err}")
                    logging.info("Sleeping for 1 minute then trying to resume")
                    for _ in tqdm(range(60)):
                        time.sleep(1)
                    retries += 1
                    continue
                except UserProtectedError as err:
                    print(err)
                    break  # get out of retry loop
                except KeyboardInterrupt:
                    session.close()
                    exit()


if __name__ == "__main__":
    main()
