from __future__ import  annotations
import json
from tqdm import tqdm

from twitscan import query

async def main() -> None:
    user_ids : list[int] = []
    async for user in query.all_users():
        user_ids.append(user[0])

    engagements : dict[int, list[dict[str, int]]] = {}
    for user in tqdm(user_ids):
        async for eng in query.engagement_for(user):
            info = eng.serialize()
            if user in engagements.keys():
                engagements[user].append(info)
            else:
                engagements[user] = [info]

    with open('data/engagements.json', 'w') as f:
        json.dump(engagements, f, indent=4, sort_keys=True)

    await query.session.close()
