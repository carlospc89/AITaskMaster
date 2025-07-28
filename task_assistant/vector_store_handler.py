# task_assistant/vector_store_handler.py
import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from .logger_config import log
import pickle


class VectorStoreHandler:
    def __init__(self, model, index_path="task_master_index.faiss", mapping_path="doc_mapping.pkl"):
        """
        Initializes the handler with a pre-loaded model.
        """
        self.index_path = index_path
        self.mapping_path = mapping_path
        # The model is now passed in, not loaded here
        self.model = model
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.doc_id_map = {}
        self.next_id = 0

        self.load_index()

    # ... (the rest of the file remains unchanged) ...
    def load_index(self):
        if os.path.exists(self.index_path) and os.path.exists(self.mapping_path):
            log.info(f"Loading existing FAISS index from {self.index_path}")
            self.index = faiss.read_index(self.index_path)
            with open(self.mapping_path, 'rb') as f:
                self.doc_id_map = pickle.load(f)
            self.next_id = max(self.doc_id_map.keys()) + 1 if self.doc_id_map else 0
        else:
            log.info("No existing index found. Creating a new one.")
            self.index = faiss.IndexFlatL2(self.dimension)

    def save_index(self):
        log.info(f"Saving FAISS index to {self.index_path}")
        faiss.write_index(self.index, self.index_path)
        with open(self.mapping_path, 'wb') as f:
            pickle.dump(self.doc_id_map, f)

    def add_document(self, text: str):
        try:
            embedding = self.model.encode([text])
            if embedding.ndim == 1:
                embedding = np.expand_dims(embedding, axis=0)
            self.index.add(embedding)
            self.doc_id_map[self.next_id] = text
            self.next_id += 1
            self.save_index()
            log.info("Successfully added a new document to the vector store.")
        except Exception as e:
            log.error(f"Failed to add document to vector store: {e}", exc_info=True)

    def search(self, query: str, k: int = 3) -> list[str]:
        if self.index.ntotal == 0:
            return []
        try:
            query_embedding = self.model.encode([query])
            if query_embedding.ndim == 1:
                query_embedding = np.expand_dims(query_embedding, axis=0)
            distances, indices = self.index.search(query_embedding, k)
            results = [self.doc_id_map[i] for i in indices[0] if i in self.doc_id_map]
            log.info(f"Vector search for query '{query}' returned {len(results)} results.")
            return results
        except Exception as e:
            log.error(f"Failed during vector search: {e}", exc_info=True)
            return []
