# task_assistant/data_ingestor.py
import json
from datetime import datetime
import hashlib
from .logger_config import log


class DataIngestor:
    def __init__(self, db_connection, vector_store):
        """
        Initializes the DataIngestor with active database and vector store connections.
        """
        self.conn = db_connection
        self.vector_store = vector_store

    def _calculate_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def _check_source_exists(self, content_hash: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM source_documents WHERE content_hash = ?", (content_hash,))
        return cursor.fetchone() is not None

    def ingest_data(self, source_name: str, content: str, tasks: list[dict]):
        """
        Handles the end-to-end process of ingesting a new document and its tasks.
        """
        content_hash = self._calculate_hash(content)
        if self._check_source_exists(content_hash):
            log.warning("Attempted to insert a duplicate source document. Operation cancelled.")
            return

        try:
            with self.conn:
                cursor = self.conn.cursor()
                processed_at = datetime.now()

                # 1. Insert into source_documents table
                cursor.execute(
                    "INSERT INTO source_documents (source_name, content_hash, processed_at) VALUES (?, ?, ?)",
                    (source_name, content_hash, processed_at)
                )
                source_document_id = cursor.lastrowid

                # 2. Insert tasks into action_items table
                created_at = datetime.now()
                for task in tasks:
                    task_json = json.dumps(task)
                    cursor.execute(
                        "INSERT INTO action_items (source_document_id, task_data, created_at) VALUES (?, ?, ?)",
                        (source_document_id, task_json, created_at)
                    )
            log.info(f"SUCCESS: Inserted {len(tasks)} tasks into SQLite for source '{source_name}'.")

            # 3. Add the document content to the vector store
            if not source_name.startswith("Jira Import"):
                self.vector_store.add_document(content)

        except Exception as e:
            log.error(f"DATABASE ERROR during ingest for source '{source_name}': {e}", exc_info=True)
