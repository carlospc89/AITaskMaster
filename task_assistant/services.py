# task_assistant/services.py
import streamlit as st
import os
from .logger_config import log
from .database_handler import DatabaseHandler
from .vector_store_handler import VectorStoreHandler
from .agent import Agent
from .rules_engine import RulesEngine
from .data_ingestor import DataIngestor  # Import the new DataIngestor
from langchain_ollama.chat_models import ChatOllama
from sentence_transformers import SentenceTransformer


# --- Cached Resources ---

@st.cache_resource
def load_embedding_model(model_name='all-MiniLM-L6-v2'):
    """Loads and caches the sentence transformer model."""
    log.info(f"Loading sentence transformer model '{model_name}'...")
    model = SentenceTransformer(model_name)
    log.info("Sentence transformer model loaded.")
    return model


@st.cache_resource
def load_llm_model(model_name="mistral"):
    """Loads and caches the main Language Model."""
    log.info(f"Loading LLM '{model_name}'...")
    model = ChatOllama(model=model_name)
    log.info("LLM loaded.")
    return model


# --- Main Initialization Function ---

def initialize_services():
    """
    Initializes all application services and stores them in session_state.
    """
    if "services_initialized" not in st.session_state:
        log.info("--- Initializing all services for the first time ---")

        embedding_model = load_embedding_model()
        llm = load_llm_model(os.getenv("OLLAMA_MODEL", "mistral"))

        # Initialize handlers that don't depend on others
        db_handler = DatabaseHandler()
        vector_store = VectorStoreHandler(model=embedding_model)

        # THE FIX: Initialize the DataIngestor with the required connections
        data_ingestor = DataIngestor(
            db_connection=db_handler.get_connection(),
            vector_store=vector_store
        )

        # Store all services in session_state
        st.session_state.db_handler = db_handler
        st.session_state.vector_store = vector_store
        st.session_state.data_ingestor = data_ingestor  # Store the new ingestor
        st.session_state.agent = Agent(model=llm)
        st.session_state.rules_engine = RulesEngine()

        st.session_state.services_initialized = True
        log.info("--- All services initialized successfully ---")