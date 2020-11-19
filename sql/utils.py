from sqlite3 import Connection

def print_schema(connection: Connection):
    for (table_name,) in connection.execute(
        """
        SELECT NAME FROM SQLITE_MASTER WHERE TYPE='table' ORDER BY NAME;
        """
    ):
        print("{}:".format(table_name))
        for (
            column_id,
            column_name,
            column_type,
            column_not_null,
            column_default,
            column_pk,
        ) in connection.execute("PRAGMA table_info('{}');".format(table_name)):
            print(
                "  {id}: {name}({type}){null}{default}{pk}".format(
                    id=column_id,
                    name=column_name,
                    type=column_type,
                    null=" not null" if column_not_null else "",
                    default=" [{}]".format(column_default) if column_default else "",
                    pk=" *{}".format(column_pk) if column_pk else "",
                )
            )
        print()