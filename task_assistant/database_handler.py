# task_assistant/database_handler.py
import sqlite3
import pandas as pd
import json
from datetime import datetime, date

# Use the correct relative import for intra-package modules
from .logger_config import log


class DatabaseHandler:
    """
    Manages the SQLite database connection and core CRUD operations (Read, Update, Delete).
    Data ingestion is handled by the DataIngestor class.
    """

    def __init__(self, db_name="task_master.db"):
        try:
            self.conn = sqlite3.connect(db_name, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            log.error(f"Database connection error: {e}")
            raise
        self._create_tables()

    def get_connection(self):
        """Provides direct access to the connection object for other services."""
        return self.conn

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
                        task_data TEXT NOT NULL,
                        created_at DATETIME NOT NULL,
                        FOREIGN KEY (source_document_id) REFERENCES source_documents (id)
                    );
                """)
        except sqlite3.Error as e:
            log.error(f"Error creating tables: {e}")

    def get_all_action_items_as_df(self) -> pd.DataFrame:
        query = "SELECT id, task_data, created_at FROM action_items ORDER BY id DESC"

        try:
            rows = self.conn.execute(query).fetchall()
        except sqlite3.OperationalError:
            return self.get_empty_df()

        if not rows:
            return self.get_empty_df()

        data_list = []
        for row in rows:
            try:
                task_data = json.loads(row['task_data'])
                flat_record = {
                    'id': row['id'],
                    'created_at': row['created_at'],
                    'task_description': task_data.get('task_description', task_data.get('task')),
                    'due_date': task_data.get('due_date'),
                    'project': task_data.get('project'),
                    'priority': task_data.get('priority'),
                    'status': task_data.get('status', 'To Do')
                }
                data_list.append(flat_record)
            except (json.JSONDecodeError, TypeError) as e:
                log.error(f"Could not parse JSON for row ID {row.get('id', 'N/A')}: {e}")
                continue

        if not data_list:
            return self.get_empty_df()

        expected_cols = [
            'id', 'task_description', 'due_date', 'project',
            'priority', 'status', 'created_at'
        ]
        df = pd.DataFrame.from_records(data_list, columns=expected_cols)

        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
        df['due_date'] = pd.to_datetime(df['due_date'], errors='coerce')

        return df

    def get_empty_df(self) -> pd.DataFrame:
        columns = [
            'id', 'task_description', 'due_date', 'project',
            'priority', 'status', 'created_at'
        ]
        return pd.DataFrame(columns=columns)

    def update_action_item(self, item_id: int, updates: dict):
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute("SELECT task_data FROM action_items WHERE id = ?", (item_id,))
                result = cursor.fetchone()
                if not result:
                    return

                current_task_data = json.loads(result['task_data'])

                for key, value in updates.items():
                    if isinstance(value, (pd.Timestamp, date)):
                        current_task_data[key] = value.strftime('%Y-%m-%d')
                    else:
                        current_task_data[key] = value

                updated_task_json = json.dumps(current_task_data)

                cursor.execute("UPDATE action_items SET task_data = ? WHERE id = ?", (updated_task_json, item_id))
        except sqlite3.Error as e:
            log.error(f"DB: DATABASE ERROR during JSON update for ID {item_id}: {e}")

    def delete_action_items(self, item_ids: list[int]):
        if not item_ids: return
        safe_item_ids = [int(i) for i in item_ids]
        placeholders = ", ".join("?" for _ in safe_item_ids)
        query = f"DELETE FROM action_items WHERE id IN ({placeholders})"
        try:
            with self.conn:
                self.conn.execute(query, safe_item_ids)
        except sqlite3.Error as e:
            log.error(f"DATABASE ERROR during deletion: {e}")

    def drop_all_tables(self):
        try:
            with self.conn:
                self.conn.execute("DROP TABLE IF EXISTS action_items")
                self.conn.execute("DROP TABLE IF EXISTS source_documents")
            self._create_tables()
        except sqlite3.Error as e:
            log.error(f"Failed to drop tables: {e}")