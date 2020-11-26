from argparse import ArgumentParser
from twitscan.errors import UserProtectedError
from twitscan.scanner import TwitterUser
from tqdm import tqdm

parser = ArgumentParser()
parser.add_argument(
    "-d", "--debug", action="store_true", default=False, help="run in debug mode"
)

if __name__ == "__main__":
    args = parser.parse_args()
    with open("data/users.txt", "r") as file:
        users = file.read().split("\n")

    for user in users:
        try:
            twitter_user = TwitterUser(screen_name=user, debug_mode=args.debug)
        except UserProtectedError:
            continue
        followers = twitter_user.followers
        for follower_id in tqdm(followers):
            try:
                TwitterUser(user_id=follower_id, debug_mode=args.debug)
            except UserProtectedError as err:
                print(err)
