from argparse import ArgumentParser
from twitscan.scanner import UserScanner

parser = ArgumentParser()
parser.add_argument("user", type=str, default="", help="user to analyse")
parser.add_argument(
    "-d", "--debug", action="store_true", default=False, help="run in debug mode"
)

if __name__ == "__main__":
    args = parser.parse_args()
    u = UserScanner(args.user, debug_mode=args.debug)
