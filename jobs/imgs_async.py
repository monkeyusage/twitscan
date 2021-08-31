"""this job takes users and download their profile pictures along with their followers's """
from __future__ import annotations

from os import environ, listdir
from sys import argv

from twitscan import query
from twitscan.models import TwitscanUser
from aiohttp import ClientSession
from aiofiles import open
from asyncio import Queue, QueueEmpty, create_task, gather

API_KEY = environ["scraperapi_proxy"]


async def download(client: ClientSession, user: TwitscanUser) -> None:
    url = user.user_picture_url.replace("_normal", "_400x400")
    if not url:
        return
    unlimited_url = f"http://api.scraperapi.com?api_key={API_KEY}&url={url}"
    async with client.get(unlimited_url) as response:
        if response.status != 200:
            print(f"error with user {user}")
            import pdb;pdb.set_trace()
            return
        file = await open(f"imgs/profiles/{user.screen_name}.jpeg", mode="wb")
        await file.write(await response.read())
        await file.close()


async def worker(client: ClientSession, queue: Queue[TwitscanUser]) -> None:
    while True:
        try:
            user = queue.get_nowait()
        except QueueEmpty:
            break
        await download(client, user)
        queue.task_done()


async def main():
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

    user_queue: Queue[TwitscanUser] = Queue()
    for user in users:
        user_queue.put_nowait(user)

    WORKERS = 5
    async with ClientSession() as client:
        tasks = [create_task(worker(client, user_queue)) for _ in range(WORKERS)]
        await user_queue.join()
        await gather(*tasks)
