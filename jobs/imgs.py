"""this job takes a hundred followers of two given Users and spits out an excel file with their profile pics"""
from __future__ import annotations

import os
import sys

import pandas as pd
from tqdm import tqdm
from tweepy.models import User

sys.path.append("../twitscan")
from twitscan import api, query
from twitscan.models import TwitscanUser


async def follower_pic_urls(user: TwitscanUser) -> str:
    """queries list of followers twitter ids from database
    gets the first 100 profile pic urls in a list & returns
    comma separated items found. if not enough found make list
    hundred items long anyway"""
    followers_uids: list[int] = await query.followers(user)
    counter: int = 0
    data: list[str] = []
    for f_uid in tqdm(followers_uids):
        try:
            user: User = api.get_user(user_id=f_uid)
        except:
            continue
        if isinstance(user.profile_image_url, str) and user.profile_image_url != "":
            counter += 1
            data.append(user.profile_image_url)
        if counter >= 100:
            break
    if len(data) == 100:
        return ",".join(data)
    while len(data) < 100:
        data.append("")
    assert len(data) == 100, f'data got len {len(data)}'
    return ",".join(data)


async def main() -> None:
    if not os.path.exists("data/excel"):
        os.makedirs("data/excel", exist_ok=True)
    assert (
        len(sys.argv) > 1
    ), "you must input at least one valid TwitScanUser from your db"
    users: list[TwitscanUser] = []
    for user in sys.argv[1:]:
        maybe_user = await query.user_by_screen_name(user)
        users.append(maybe_user)
    assert (
        None not in users
    ), "there is at least one invalid Twitter Screen Name, user should already be in database"

    with open("data/excel/image_urls.csv", "w") as f:
        hundred_cols = ",".join([f"follower_{num}" for num in range(1, 101)])
        f.write(f"name,{hundred_cols}\n")
        for user in users:
            user_name = user.screen_name
            follower_pics = follower_pic_urls(user)
            f.write(f"{user_name},{follower_pics}\n")

    dataframe = pd.read_csv("data/excel/image_urls.csv")
    dataframe.to_excel("data/excel/image_urls.xlsx", index=False)
    os.remove('data/excel/image_urls.csv')
    await query.async_session.close()