CREATE TABLE users (
    -- ids
    user_id INTEGER NOT NULL PRIMARY KEY,
    screen_name VARCHAR(51) NOT NULL,
    -- datetime value
    created_at TIMESTAMP NOT NULL,
    -- counts
    favorites_count INTEGER NOT NULL,
    statuses_count INTEGER NOT NULL, -- tweets | retweets
    friends_count INTEGER NOT NULL, -- friend is whom user follows
    followers_count INTEGER NOT NULL,
    -- bools
    is_verified INTEGER NOT NULL,
)

CREATE TABLE statuses (
    -- ids
    status_id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    -- max text is 280 chars
    status_text VARCHAR(281) NOT NULL,
    -- datetime value
    created_at TIMESTAMP NOT NULL,
    -- counts
    favorite_count INTEGER NOT NULL,
    retweet_count INTEGER NOT NULL,
    -- reply ids
    in_reply_to_status_id INTEGER,
    in_reply_to_user_id INTEGER,
    -- bools
    is_retweet INTEGER NOT NULL -- actually bool
)

CREATE TABLE status_mentions (
    mention_id INTEGER NOT NULL PRIMARY KEY,
    status_id INTEGER NOT NULL,
    mentioned_user_id INTEGER NOT NULL,
)

CREATE TABLE friends (
    relation_id INTEGER NOT NULL PRIMARY KEY,
    followed_user_id INTEGER NOT NULL,
    friend_user_id INTEGER NOT NULL,
)

CREATE TABLE likes (
    like_id INTEGER NOT NULL PRIMARY KEY,
    status_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL
)