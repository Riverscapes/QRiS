import sqlite3


class DBCon(sqlite3.Connection):
    """Custom connection class to enable foreign keys and return rows as dictionaries."""

    @staticmethod
    def connect(db_path: str):
        """Connect to the database and return a connection object."""
        return DBCon(db_path)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.row_factory = self.dict_factory  # <-- Add this line
        self.execute("PRAGMA foreign_keys = ON;")

    def dict_factory(self, cursor: sqlite3.Cursor, row):
        """Custom row factory to return rows as dictionaries."""
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

    def cursor(self, *args, **kwargs):
        """Override the cursor to use the dict_factory as the row_factory."""
        cur = super().cursor(*args, **kwargs)
        cur.row_factory = self.dict_factory
        return cur

    def load_data(self, key: str) -> dict:
        """Load data from the database based on the provided key."""
        cursor = self.cursor()
        cursor.execute("SELECT * FROM data WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row if row else {}
