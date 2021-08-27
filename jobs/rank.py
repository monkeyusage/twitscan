from __future__ import annotations
import json
from tqdm import tqdm
from sys import argv
from twitscan import query


def main() -> None:
    user_ids: list[int] = []
    
    for user in tqdm(argv[1:]):
        maybe_u_id = query.user_by_screen_name(user)
        if maybe_u_id is None:
            print("Did not find user in Database, skipping to the next one")
            continue    
        user_ids.append(maybe_u_id[0])
    
