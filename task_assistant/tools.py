from datetime import datetime
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
    Takes a specific date string (e.g., "2025-08-01", "August 1, 2025")
    and validates and formats it into the required YYYY-MM-DD format.
    This tool should NOT be called with relative terms like "tomorrow",
    as that logic is handled by the AI agent before calling this tool.

    Args:
        date_text: A string representing a specific, non-relative date.

    Returns:
        The date in YYYY-MM-DD format, or None if parsing fails.
    """
    if not date_text:
        return None
    try:
        # Use dateutil.parser which is excellent for specific, non-relative dates.
        parsed_date = dateutil_parser.parse(date_text)
        return parsed_date.strftime('%Y-%m-%d')
    except (ValueError, TypeError) as e:
        # This will catch any strings that cannot be resolved to a specific date.
        print(f"Error parsing date '{date_text}': {e}")
        return None

all_tools = [tavily_tool, parse_natural_date]