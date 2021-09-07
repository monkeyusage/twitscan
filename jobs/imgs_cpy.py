import pandas as pd
from os import listdir
import shutil

df = pd.read_csv("data/ranked.tsv", sep="\t")
followers: list[str] = df["follower"].to_list()
pics = set(name.replace(".jpeg", "") for name in listdir("imgs/profiles"))

for follower in followers:
    if follower in pics:
        shutil.copyfile(
            f"imgs/profiles/{follower}.jpeg", f"data/images/{follower}.jpeg"
        )
