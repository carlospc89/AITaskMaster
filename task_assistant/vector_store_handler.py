# task_assistant/vector_store_handler.py
import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from .logger_config import log
import pickle


class VectorStoreHandler:
    def __init__(self, index_path="task_master_index.faiss", mapping_path="doc_mapping.pkl",
                 model_name='all-MiniLM-L6-v2'):
        """
        Initializes the handler for the FAISS vector store.

        Args:
            index_path (str): The file path to save/load the FAISS index.
            mapping_path (str): Path to save/load the index-to-document mapping.
            model_name (str): The name of the sentence-transformer model to use.
        """
        self.index_path = index_path
        self.mapping_path = mapping_path
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.doc_id_map = {}  # Maps FAISS index ID to document text
        self.next_id = 0

        self.load_index()

    def load_index(self):
        """Loads the FAISS index and document mapping from disk if they exist."""
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
        """Saves the current FAISS index and document mapping to disk."""
        log.info(f"Saving FAISS index to {self.index_path}")
        faiss.write_index(self.index, self.index_path)
        with open(self.mapping_path, 'wb') as f:
            pickle.dump(self.doc_id_map, f)

    def add_document(self, text: str):
        """
        Adds a document's text to the vector store.
        """
        try:
            embedding = self.model.encode([text])

            if embedding.ndim == 1:
                embedding = np.expand_dims(embedding, axis=0)

            self.index.add(embedding)
            # Store the document text with the current index ID
            self.doc_id_map[self.next_id] = text
            self.next_id += 1

            self.save_index()
            log.info(f"Successfully added a new document to the vector store.")
        except Exception as e:
            log.error(f"Failed to add document to vector store: {e}", exc_info=True)

    def search(self, query: str, k: int = 3) -> list[str]:
        """
        Searches the vector store for the most relevant documents.
        """
        if self.index.ntotal == 0:
            return []

        try:
            query_embedding = self.model.encode([query])

            if query_embedding.ndim == 1:
                query_embedding = np.expand_dims(query_embedding, axis=0)

            # Search the index for the top k most similar vectors
            distances, indices = self.index.search(query_embedding, k)

            # Retrieve the documents using the mapping
            results = [self.doc_id_map[i] for i in indices[0] if i in self.doc_id_map]

            log.info(f"Vector search for query '{query}' returned {len(results)} results.")
            return results
        except Exception as e:
            log.error(f"Failed during vector search: {e}", exc_info=True)
            return []
