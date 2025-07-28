# task_assistant/tools.py
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional
from dateutil import parser as dateutil_parser
from langchain.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from dotenv import load_dotenv

load_dotenv()

tavily_tool = TavilySearchResults(max_results=4)

@tool
def parse_natural_date(date_text: str) -> Optional[str]:
    """
    Takes a specific date string (e.g., "2025-08-01", "tomorrow")
    and validates and formats it into the required YYYY-MM-DD format.
    It has special handling for common relative terms.

    Args:
        date_text: A string representing a specific date.

    Returns:
        The date in YYYY-MM-DD format, or None if parsing fails.
    """
    if not date_text:
        return None

    # --- THIS IS THE FIX ---
    # Add explicit handling for common, simple relative terms first.
    today = datetime.now().date()
    lower_text = date_text.lower().strip()

    if lower_text == "tomorrow":
        return (today + timedelta(days=1)).strftime('%Y-%m-%d')
    if lower_text == "today":
        return today.strftime('%Y-%m-%d')
    if lower_text == "yesterday":
        return (today - timedelta(days=1)).strftime('%Y-%m-%d')
    # --- END FIX ---

    try:
        # If it's not a simple term, use the robust dateutil parser.
        parsed_date = dateutil_parser.parse(date_text)
        return parsed_date.strftime('%Y-%m-%d')
    except (ValueError, TypeError) as e:
        st.error(f"Error parsing date '{date_text}': {e}")
        return None

all_tools = [tavily_tool, parse_natural_date]
