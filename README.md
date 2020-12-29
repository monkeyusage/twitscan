# twitscan

This library lets users retrieve data from twitter user and followers interactions with ease.

This project requires the latest stable python version: python 3.9

Before you run the main script for the first time you need to:

    - run dev/predev to create a virtual env and install dependencies
    - store your twitter api credentials in your environment variables

Developers should also run dev\build.(bat|sh) to build the project when they're done modifying code.

scanner.py provides functions to scan twitter users and query.py provides functions to query the scanned users from your sqlalchemy/sqlite database.
Feel free to add query and scanning functions for your personal use ! Pull requests's are welcome.
 