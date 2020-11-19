import sqlite3

with open("sql/create_db.sql", "r") as query_file:
    script = query_file.read()

connection = sqlite3.connect("data/twitter.db")
with connection.cursor() as cursor:
    cursor.execute(script)
        