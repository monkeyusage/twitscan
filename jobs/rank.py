import os
from twitscan import query

async def main() -> None:
    test_user_name = os.environ['TWITSCAN_TEST_USER']
    test_user = await query.user_by_screen_name(test_user_name)
    
    await query.session.close()
