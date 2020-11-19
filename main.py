from argparse import ArgumentParser
from twitter import UserScanner
from sql.create_db import create_db

parser = ArgumentParser()
parser.add_argument("user", type=str, default="", help="user to analyse")
parser.add_argument(
    "-d", "--debug", action="store_true", default=False, help="run in debug mode"
)
parser.add_argument(
    "--db", default=":memory:", help="defines name of db for storage in data folder"
)

if __name__ == "__main__":
    args = parser.parse_args()
    connection = create_db(args.db)
    u = UserScanner(args.user, db_connection=connection, debug_mode=args.debug)
