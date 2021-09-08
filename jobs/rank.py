from __future__ import annotations

from os.path import exists
from tqdm import tqdm
from twitscan import query
import pandas as pd


def main() -> None:
    with open("data/users.txt", "r") as file:
        users = file.read().splitlines()

    columns = [
        "user",
        "follower",
        "common_entourage",
        "entourage_a",
        "entourage_b",
        "common_hashtags",
        "hashtags_a",
        "hashtags_b",
        "a_mentions_b",
        "b_mentions_a",
        "a_mentions_counter",
        "b_mentions_counter",
        "a_favs_b",
        "b_favs_a",
        "a_favs_count",
        "b_favs_count",
        "a_rt_b",
        "b_rt_a",
        "a_cmt_b",
        "b_cmt_a"
    ]

    if not exists("data/ranking.tsv"):
        with open("data/ranking.tsv", "w") as file:
            file.write("\t".join(columns) + "\n")
        already_scored_followers: dict[str, set[str]] = {}
    else:
        already_scored_followers = {}
        tmp_df = pd.read_csv("data/ranking.tsv", sep="\t")
        for user in tmp_df["user"].unique():
            already_scored_followers[user] = set(tmp_df[tmp_df["user"] == user]["follower"].values)

    with open("data/ranking.tsv", "a") as file:
        for user in users:
            if user not in already_scored_followers.keys():
                already_scored_followers[user] = set()
            maybe_user = query.user_by_screen_name(user)
            if maybe_user is None:
                print("Did not find user in Database, skipping to the next one")
                continue
            for entourage in tqdm(maybe_user.entourage):
                if not entourage.follower:
                    print("Not a follower")
                    continue
                follower = query.user_by_id(entourage.friend_follower_id)
                if follower is None:
                    print("Did not find the follower in database, must be a private profile")
                    continue
                if follower.screen_name in already_scored_followers[user]:
                    print("Follower already scored")
                    continue
                print(f"Scanning proximity between {maybe_user} and {follower}")
                proximity_info = query.proximity(maybe_user, follower)
                information = "\t".join(map(lambda info: str(info), proximity_info))
                file.write(
                    f"{maybe_user.screen_name}\t{follower.screen_name}\t{information}\n"
                )

if __name__ == "__main__":
    main()
