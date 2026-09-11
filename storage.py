"""SQLite persistence for anonymous reply routes."""

import sqlite3
from contextlib import closing
from pathlib import Path


class MessageStore:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)

    def initialize(self) -> None:
        with closing(self._connect()) as connection:
            with connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS message_routes (
                        owner_message_id INTEGER PRIMARY KEY,
                        recipient_id INTEGER NOT NULL
                    )
                    """
                )

    def save_recipient(self, owner_message_id: int, recipient_id: int) -> None:
        with closing(self._connect()) as connection:
            with connection:
                connection.execute(
                    """
                    INSERT OR REPLACE INTO message_routes (owner_message_id, recipient_id)
                    VALUES (?, ?)
                    """,
                    (owner_message_id, recipient_id),
                )

    def get_recipient(self, owner_message_id: int) -> int | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT recipient_id FROM message_routes WHERE owner_message_id = ?",
                (owner_message_id,),
            ).fetchone()
        return row[0] if row else None
