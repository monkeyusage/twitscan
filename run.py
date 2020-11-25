from argparse import ArgumentParser
from twitscan.errors import TooManyFollowersError
from twitscan.scanner import scan
from twitscan import session

parser = ArgumentParser()
parser.add_argument("user", type=str, default="", help="user to analyse")
parser.add_argument(
    "-d", "--debug", action="store_true", default=False, help="run in debug mode"
)

if __name__ == "__main__":
    args = parser.parse_args()
    try:
        scan(args.user, debug_mode=args.debug)
    except TooManyFollowersError as err:
        print(f"Caught error: {err}")