import os
import sqlite3


def get_connection() -> sqlite3.Connection:
    db_path = os.path.expanduser(os.getenv('BIRDNET_DB', '~/BirdNET-Pi/scripts/birds.db'))
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
