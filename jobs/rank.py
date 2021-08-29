from __future__ import annotations

from os.path import exists
from tqdm import tqdm
from twitscan import query


def main() -> None:
    with open("data/users.txt", "r") as file:
        users = file.read().splitlines()

    if not exists("data/ranking.tsv"):
        with open("data/ranking.tsv", "w") as file:
            file.write("user\tfollower\tscore\n")

    with open("data/ranking.tsv", "a") as file:
        for user in tqdm(users):
            maybe_user = query.user_by_screen_name(user)
            if maybe_user is None:
                print("Did not find user in Database, skipping to the next one")
                continue
            for entourage in tqdm(maybe_user.entourage):
                if not entourage.follower:
                    continue
                follower = query.user_by_id(entourage.friend_follower_id)
                if follower is None:
                    print("Did not find the follower in database")
                    continue
                score = query.proximity(maybe_user, follower)
                file.write(f"{maybe_user.screen_name}\t{follower.screen_name}\t{score}\n")
