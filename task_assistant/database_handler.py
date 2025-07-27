# task_assistant/database_handler.py
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime
from .logger_config import log
import numpy as np  # Import numpy to check for its types


class DatabaseHandler:
    def __init__(self, db_name="task_master.db"):
        try:
            self.conn = sqlite3.connect(db_name, check_same_thread=False)
        except sqlite3.Error as e:
            log.error(f"Database connection error: {e}")
            raise
        self._create_tables()

    def _create_tables(self):
        try:
            with self.conn:
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS source_documents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source_name TEXT NOT NULL,
                        content_hash TEXT UNIQUE NOT NULL,
                        processed_at DATETIME NOT NULL
                    );
                """)
                self.conn.execute("""
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
        except sqlite3.Error as e:
            log.error(f"Error creating tables: {e}")

    def update_action_item(self, item_id: int, updates: dict):
        log.info(f"DB: --- Entered update_action_item for ID: {item_id} (type: {type(item_id)}) ---")
        if not updates:
            log.warning("DB: Update dictionary is empty. Exiting function.")
            return

        sanitized_updates = {}
        for key, value in updates.items():
            if isinstance(value, pd.Timestamp):
                sanitized_updates[key] = value.strftime('%Y-%m-%d')
            else:
                sanitized_updates[key] = value

        set_clause = ", ".join([f"\"{key}\" = ?" for key in sanitized_updates.keys()])

        # THIS IS THE FIX: Explicitly convert the item_id to a standard Python int.
        safe_item_id = int(item_id) if isinstance(item_id, (np.integer, int)) else item_id

        values = list(sanitized_updates.values()) + [safe_item_id]
        query = f"UPDATE action_items SET {set_clause} WHERE id = ?"

        log.info(f"DB: Preparing to execute SQL: {query}")
        log.info(f"DB: With values: {values} (ID type: {type(safe_item_id)})")

        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute(query, values)
            log.info(
                f"DB: SUCCESS - Transaction committed for item ID: {safe_item_id}. Rows affected: {cursor.rowcount}")
        except sqlite3.Error as e:
            log.error(f"DB: DATABASE ERROR on update for item ID {safe_item_id}: {e}")

    # --- Other methods remain unchanged ---
    def get_all_action_items_as_df(self):
        df = pd.read_sql_query("SELECT * FROM action_items ORDER BY id DESC", self.conn)
        if df.empty:
            return pd.DataFrame(
                columns=['id', 'task_description', 'due_date', 'project', 'priority', 'status', 'created_at'])
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
        df['due_date'] = pd.to_datetime(df['due_date'], errors='coerce')
        return df

    def delete_action_items(self, item_ids: list[int]):
        if not item_ids:
            return
        # Convert all IDs to standard Python ints
        safe_item_ids = [int(i) for i in item_ids]
        placeholders = ", ".join("?" for _ in safe_item_ids)
        query = f"DELETE FROM action_items WHERE id IN ({placeholders})"
        try:
            with self.conn:
                self.conn.execute(query, safe_item_ids)
            log.info(f"SUCCESS: Deletion for IDs {safe_item_ids} committed.")
        except sqlite3.Error as e:
            log.error(f"DATABASE ERROR during deletion for IDs {safe_item_ids}: {e}")

    def _calculate_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def check_source_exists(self, content: str) -> bool:
        content_hash = self._calculate_hash(content)
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM source_documents WHERE content_hash = ?", (content_hash,))
        return cursor.fetchone() is not None

    def insert_data(self, source_name: str, content: str, tasks: list[dict]):
        if self.check_source_exists(content):
            log.warning("Attempted to insert a duplicate source document. Operation cancelled.")
            return
        try:
            with self.conn:
                cursor = self.conn.cursor()
                content_hash = self._calculate_hash(content)
                processed_at = datetime.now()
                cursor.execute(
                    "INSERT INTO source_documents (source_name, content_hash, processed_at) VALUES (?, ?, ?)",
                    (source_name, content_hash, processed_at)
                )
                source_document_id = cursor.lastrowid
                created_at = datetime.now()
                for task in tasks:
                    cursor.execute(
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
            log.info(f"SUCCESS: Inserted {len(tasks)} tasks for source '{source_name}'.")
        except sqlite3.Error as e:
            log.error(f"DATABASE ERROR during insert for source '{source_name}': {e}")

    def drop_all_tables(self):
        try:
            with self.conn:
                self.conn.execute("DROP TABLE IF EXISTS action_items")
                self.conn.execute("DROP TABLE IF EXISTS source_documents")
            log.info("All database tables have been dropped.")
            self._create_tables()
        except sqlite3.Error as e:
            log.error(f"Failed to drop tables: {e}")