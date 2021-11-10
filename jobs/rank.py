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
        "entourage_user",
        "entourage_follower",
        "common_hashtags",
        "hashtags_user",
        "hashtags_follower",
        "user_mentions_follower",
        "follower_mentions_user",
        "user_mentions_counter",
        "follower_mentions_counter",
        "user_favs_follower",
        "follower_favs_user",
        "user_favs_count",
        "follower_favs_count",
        "user_rt_follower",
        "follower_rt_user",
        "user_cmt_follower",
        "follower_cmt_user",
    ]

    if not exists("data/ranking.tsv"):
        with open("data/ranking.tsv", "w") as file:
            file.write("\t".join(columns) + "\n")
        already_scored_followers: dict[str, set[str]] = {}
    else:
        already_scored_followers = {}
        tmp_df = pd.read_csv("data/ranking.tsv", sep="\t")
        for user in tmp_df["user"].unique():
            already_scored_followers[user] = set(
                tmp_df[tmp_df["user"] == user]["follower"].values
            )

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
                    print(
                        "Did not find the follower in database, must be a private profile"
                    )
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
<<<<<<< HEAD

    dataframe = pd.read_csv("data/ranking.tsv", sep="\t")
    dataframe = dataframe.drop_duplicates("follower")
    #dataframe = dataframe.sort_values("score")

    dfs: list[pd.DataFrame] = []
    for user in dataframe["user"].unique():
        df = dataframe[dataframe["user"] == user]
        dfs.append(df.head(50).append(df.tail(50)))

    output = pd.concat(dfs)
    output.to_csv("data/ranked.tsv", sep="\t", index=False)
=======
>>>>>>> f87d6feeaac68202d2740f7198853200c32f7b1a


if __name__ == "__main__":
    main()
