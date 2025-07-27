# In task_assistant/utils.py

import re
import pandas as pd

def normalize_text(text: str) -> str:
    """
    Normalizes text by standardizing newlines and trimming whitespace.
    """
    normalized_text = text.replace('\r\n', '\n')
    normalized_text = normalized_text.strip()
    return normalized_text

def sanitize_df_for_streamlit(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans a Pandas DataFrame to ensure it's compatible with Streamlit's
    Arrow-based serialization. This prevents pyarrow.lib.ArrowInvalid errors.

    Args:
        df: The input DataFrame.

    Returns:
        A cleaned, safe-to-display DataFrame.
    """
    df_copy = df.copy()
    for col in df_copy.columns:
        # Handle Datetime objects
        if pd.api.types.is_datetime64_any_dtype(df_copy[col]):
            continue
        # Handle Object columns (which can contain mixed types)
        if df_copy[col].dtype == 'object':
            df_copy[col] = df_copy[col].astype(str).fillna('')
        # Handle problematic integer types (like pandas' nullable Int64DType)
        if pd.api.types.is_integer_dtype(df_copy[col]):
            df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce').fillna(0).astype(int)

    return df_copy