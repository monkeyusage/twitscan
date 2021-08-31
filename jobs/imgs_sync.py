from __future__ import annotations
from os import listdir
from sys import argv
from twitscan import query
from twitscan.models import TwitscanUser
from time import sleep
from requests import get
from random import randint

def download(user: TwitscanUser) -> None:
    url = user.user_picture_url.replace("_normal", "_400x400")
    if not url:
        return
    sleep(randint(20,30))
    print(f"Requesting {user}")
    response = get(url, stream=True)
    if not response.ok:
        print(f"error with user {user}, code: {response.status_code}")
        return
    with open(f"imgs/profiles/{user.screen_name}.jpeg", mode="wb") as file:
        for chunk in response.iter_content(1024):
            file.write(chunk)

def main():
    already_scanned = set(
        map(lambda fname: fname.replace(".jpeg", ""), listdir("imgs/profiles"))
    )
    users: list[TwitscanUser] = []
    assert argv[1:] != [], "empty argv, provide usernames please"
    for username in argv[1:]:
        user = query.user_by_screen_name(username)
        if user is None:
            print(f"{username} is not in database")
            continue
        # get the f_ids
        follower_ids = set(
            map(lambda entourage: entourage.friend_follower_id, user.entourage)
        )
        # use them to query all the user's followers
        maybe_followers: list[TwitscanUser | None] = [
            query.user_by_id(f_id) for f_id in follower_ids
        ]
        followers = [
            u
            for u in maybe_followers
            if (u is not None) and (u.screen_name not in already_scanned)
        ]
        users.extend(followers)

    for user in users:
        download(user)