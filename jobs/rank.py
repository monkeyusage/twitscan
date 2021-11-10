from __future__ import annotations

from os.path import exists
from tqdm import tqdm
from twitscan import query
import pandas as pd


def main() -> None:
    with open("data/users.txt", "r") as file:
        users = file.read().splitlines()

    if not exists("data/ranking.tsv"):
        with open("data/ranking.tsv", "w") as file:
            file.write(
                "user\tfollower\tcommon_entourage\tcommon_hashtags\ttotal_mentions\ttotal_favs\ttotal_rts\ttotal_cmts\tscore\n"
            )
        already_scored_users: set[str] = set()
    else:
        already_scored_users = set(
            pd.read_csv("data/ranking.tsv", sep="\t")["follower"].values
        )

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
                if follower.screen_name in already_scored_users:
                    print("Follower already scored")
                    continue
                (
                    common_entourage,
                    common_hashtags,
                    total_mentions,
                    total_favs,
                    total_rts,
                    total_cmts,
                ) = query.proximity(maybe_user, follower)
                file.write(
                    f"{maybe_user.screen_name}\t{follower.screen_name}\t{common_entourage}\t{common_hashtags}\t{total_mentions}\t{total_favs}\t{total_rts}\t{total_cmts}\t\n"
                )

    dataframe = pd.read_csv("data/ranking.tsv", sep="\t")
    dataframe = dataframe.drop_duplicates("follower")
    #dataframe = dataframe.sort_values("score")

    dfs: list[pd.DataFrame] = []
    for user in dataframe["user"].unique():
        df = dataframe[dataframe["user"] == user]
        dfs.append(df.head(50).append(df.tail(50)))

    output = pd.concat(dfs)
    output.to_csv("data/ranked.tsv", sep="\t", index=False)


if __name__ == "__main__":
    main()
