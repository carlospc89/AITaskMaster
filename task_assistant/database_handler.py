import sqlite3
import hashlib
import pandas as pd
from datetime import datetime
from .logger_config import log


class DatabaseHandler:
    def __init__(self, db_name="task_master.db"):
        """Initializes the database connection and creates tables if they don't exist."""
        try:
            self.conn = sqlite3.connect(db_name, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self._create_tables()
            log.info(f"Successfully connected to database '{db_name}'")
        except sqlite3.Error as e:
            log.error(f"Database connection error: {e}")
            raise

    def _create_tables(self):
        """Creates the necessary tables if they do not already exist."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS source_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name TEXT NOT NULL,
                content_hash TEXT UNIQUE NOT NULL,
                processed_at DATETIME NOT NULL
            );
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS action_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_document_id INTEGER NOT NULL,
                task_description TEXT NOT NULL,
                due_date TEXT,
                priority TEXT NOT NULL,
                project TEXT,
                status TEXT NOT NULL DEFAULT 'To Do',
                created_at DATETIME NOT NULL,
                FOREIGN KEY (source_document_id) REFERENCES source_documents (id)
            );
        """)
        self.conn.commit()

    def _calculate_hash(self, content: str) -> str:
        """Calculates the SHA-256 hash of a string."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def check_source_exists(self, content: str) -> bool:
        """Checks if a source document with the same content hash already exists."""
        content_hash = self._calculate_hash(content)
        self.cursor.execute("SELECT id FROM source_documents WHERE content_hash = ?", (content_hash,))
        return self.cursor.fetchone() is not None

    def insert_data(self, source_name: str, content: str, tasks: list[dict]):
        """Inserts a new source document and its associated action items."""
        if self.check_source_exists(content):
            log.warning("Attempted to insert a duplicate source document. Operation cancelled.")
            return

        try:
            content_hash = self._calculate_hash(content)
            processed_at = datetime.now()
            self.cursor.execute(
                "INSERT INTO source_documents (source_name, content_hash, processed_at) VALUES (?, ?, ?)",
                (source_name, content_hash, processed_at)
            )
            source_document_id = self.cursor.lastrowid
            created_at = datetime.now()
            for task in tasks:
                self.cursor.execute(
                    "INSERT INTO action_items (source_document_id, task_description, due_date, priority, project, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        source_document_id,
                        task.get("task"),
                        task.get("due_date"),
                        task.get("priority"),
                        task.get("project"),
                        created_at
                    )
                )
            self.conn.commit()
            log.info(f"Inserted {len(tasks)} action items for source ID {source_document_id}.")
        except sqlite3.Error as e:
            log.error(f"Failed to insert data into database: {e}")
            self.conn.rollback()

    def get_all_action_items_as_df(self):
        """Fetches all action items and returns them as a pandas DataFrame."""
        query = "SELECT id, task_description, due_date, project, priority, status, created_at FROM action_items ORDER BY id DESC"
        df = pd.read_sql_query(query, self.conn)

        # Convert date columns to datetime objects for the UI
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
        df['due_date'] = pd.to_datetime(df['due_date'], format='%d/%m/%Y', errors='coerce')
        return df

    def update_action_item(self, item_id: int, updates: dict):
        """Updates specific fields for a given action item."""
        updates.pop("id", None)
        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values()) + [item_id]
        query = f"UPDATE action_items SET {set_clause} WHERE id = ?"

        try:
            self.cursor.execute(query, values)
            self.conn.commit()
            log.info(f"Updated item {item_id} with new data: {updates}")
        except sqlite3.Error as e:
            log.error(f"Failed to update item {item_id}: {e}")
            self.conn.rollback()

    def delete_action_items(self, item_ids: list[int]):
        """Deletes action items by their IDs."""
        if not item_ids:
            return

        placeholders = ", ".join("?" for _ in item_ids)
        query = f"DELETE FROM action_items WHERE id IN ({placeholders})"

        try:
            self.cursor.execute(query, item_ids)
            self.conn.commit()
            log.info(f"Deleted items with IDs: {item_ids}")
        except sqlite3.Error as e:
            log.error(f"Failed to delete items: {e}")
            self.conn.rollback()