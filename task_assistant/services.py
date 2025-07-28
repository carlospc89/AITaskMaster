# task_assistant/services.py
import streamlit as st
import os
from .logger_config import log
from .database_handler import DatabaseHandler
from .vector_store_handler import VectorStoreHandler
from .agent import Agent
from .rules_engine import RulesEngine
from langchain_ollama.chat_models import ChatOllama
from sentence_transformers import SentenceTransformer


# --- Cached Resources ---

@st.cache_resource
def load_embedding_model(model_name='all-MiniLM-L6-v2'):
    """Loads and caches the sentence transformer model."""
    log.info(f"Loading sentence transformer model '{model_name}' for the first time...")
    model = SentenceTransformer(model_name)
    log.info("Sentence transformer model loaded successfully.")
    return model


@st.cache_resource
def load_llm_model(model_name="mistral"):
    """Loads and caches the main Language Model."""
    log.info(f"Loading LLM '{model_name}' for the first time...")
    model = ChatOllama(model=model_name)
    log.info("LLM loaded successfully.")
    return model


# --- Main Initialization Function ---

def initialize_services():
    """
    Initializes all application services if they don't already exist in the
    session state. This function is safe to call on every page.
    """
    if "services_initialized" not in st.session_state:
        log.info("--- Initializing all services for the first time ---")

        # Load heavy, cached models
        embedding_model = load_embedding_model()
        llm = load_llm_model(os.getenv("OLLAMA_MODEL", "mistral"))

        # Initialize handlers and agents
        st.session_state.vector_store = VectorStoreHandler(model=embedding_model)
        st.session_state.db_handler = DatabaseHandler(vector_store=st.session_state.vector_store)
        st.session_state.agent = Agent(model=llm)
        st.session_state.rules_engine = RulesEngine()

        st.session_state.services_initialized = True
        log.info("--- All services initialized and stored in session_state ---")
