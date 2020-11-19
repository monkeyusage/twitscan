import sqlite3
from sqlite3 import Connection
from argparse import ArgumentParser


def print_schema(connection: Connection):
    for (table_name,) in connection.execute(
        """
        SELECT NAME FROM SQLITE_MASTER WHERE TYPE='table' ORDER BY NAME;
        """
    ):
        print("{}:".format(table_name))
        for (
            column_id,
            column_name,
            column_type,
            column_not_null,
            column_default,
            column_pk,
        ) in connection.execute("PRAGMA table_info('{}');".format(table_name)):
            print(
                "  {id}: {name}({type}){null}{default}{pk}".format(
                    id=column_id,
                    name=column_name,
                    type=column_type,
                    null=" not null" if column_not_null else "",
                    default=" [{}]".format(column_default) if column_default else "",
                    pk=" *{}".format(column_pk) if column_pk else "",
                )
            )
        print()


def get_connection(db_name: str = ":memory:") -> Connection:
    db_path = "data/" + db_name if not db_name == ":memory:" else db_name
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    with conn:
        # Create all tables if they don't exist
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                -- ids
                user_id INTEGER NOT NULL PRIMARY KEY,
                screen_name VARCHAR(51) NOT NULL,
                -- datetime value
                created_at TIMESTAMP NOT NULL,
                -- counts
                favorites_count INTEGER NOT NULL,
                statuses_count INTEGER NOT NULL, -- tweets | retweets
                friends_count INTEGER NOT NULL, -- friend is whom user follows
                followers_count INTEGER NOT NULL,
                -- bools
                is_verified INTEGER NOT NULL
            )"""
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS statuses (
                -- ids
                status_id INTEGER NOT NULL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                -- max text is 280 chars
                status_text VARCHAR(281) NOT NULL,
                -- datetime value
                created_at TIMESTAMP NOT NULL,
                -- counts
                favorite_count INTEGER NOT NULL,
                retweet_count INTEGER NOT NULL,
                -- reply ids
                in_reply_to_status_id INTEGER,
                in_reply_to_user_id INTEGER,
                -- bools
                is_retweet INTEGER NOT NULL -- actually bool
            )"""
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS status_mentions (
                mention_id INTEGER NOT NULL PRIMARY KEY,
                status_id INTEGER NOT NULL,
                mentioned_user_id INTEGER NOT NULL
            )"""
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS friends (
                friendship_id INTEGER NOT NULL PRIMARY KEY,
                following_user_id INTEGER NOT NULL,
                friend_user_id INTEGER NOT NULL
            )"""
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS followers (
                followership_id INTEGER NOT NULL PRIMARY KEY,
                followed_user_id INTEGER NOT NULL,
                follower_user_id INTEGER NOT NULL
            )"""
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS likes (
                like_id INTEGER NOT NULL PRIMARY KEY,
                status_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL
            )"""
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS retweets (
                retweet_id INTEGER NOT NULL PRIMARY KEY,
                status_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL
            )"""
        )

    return conn


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--db", default=":memory:", help="defines name of db for storage in data folder"
    )

    args = parser.parse_args()
    if args.db == ":memory":
        print(
            "Create in-memory database, for persistant database specify db name with --db "
        )
    connection = get_connection(args.db)
    print_schema(connection)
