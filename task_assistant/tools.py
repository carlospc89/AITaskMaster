# In task_assistant/tools.py
import parsedatetime
from datetime import datetime
from dateutil import parser as dateutil_parser
from langchain.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from dotenv import load_dotenv


load_dotenv()

# Initialize the web search tool
tavily_tool = TavilySearchResults(max_results=4)

@tool
def parse_natural_date(date_text: str) -> str:
    """
    Parse a natural language date and return it in DD/MM/YYYY format.

    Args:
        date_text: Natural language date string (e.g., "next Friday", "tomorrow")

    Returns:
        Date in DD/MM/YYYY format or an error message if parsing fails.
    """
    try:
        # First, try with dateutil for more structured dates
        try:
            parsed_date = dateutil_parser.parse(date_text, fuzzy=True)
            return parsed_date.strftime("%d/%m/%Y")
        except ValueError:
            # Fall back to parsedatetime for more natural language
            cal = parsedatetime.Calendar()
            time_struct, parse_status = cal.parse(date_text)
            if parse_status != 0:
                return datetime(*time_struct[:6]).strftime("%d/%m/%Y")
            else:
                return f"Could not parse the date: {date_text}"
    except Exception as e:
        return f"Error parsing date '{date_text}': {str(e)}"

# A list of all tools we will use
all_tools = [tavily_tool, parse_natural_date]