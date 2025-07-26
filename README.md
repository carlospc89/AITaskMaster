# Task Master AI

Task Master AI is an intelligent assistant that uses a Large Language Model (LLM) to extract, parse, and prioritize action items from meeting notes and other documents. It features a simple web interface built with Streamlit and a configurable rules engine for custom task prioritization.

## Features

-   Extracts action items from text, `.docx`, `.txt`, and `.pdf` files.
-   Uses a local LLM via Ollama for privacy and control.
-   Prioritizes tasks based on custom keywords defined in `config.yaml`.
-   Simple, interactive UI built with Streamlit.
-   Structured logging to `app.log` for easy debugging.

## Setup and Installation

### Prerequisites

-   Python 3.9+
-   [Ollama](https://ollama.com/) installed and running with a model (e.g., `ollama run mistral`).
-   `uv` for package management (`pip install uv`).

### Installation Steps

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd task_master_project
    ```

2.  **Create and activate the virtual environment:**
    ```bash
    uv venv
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    uv pip install -r requirements.txt
    ```

4.  **Install the project in editable mode:**
    ```bash
    uv pip install -e .
    ```

## Configuration

1.  **Environment Variables (`.env`):**
    Create a `.env` file in the root directory and specify the Ollama model to use:
    ```env
    OLLAMA_MODEL="mistral"
    ```

2.  **Rules Engine (`config.yaml`):**
    Modify `config.yaml` to define your custom priority rules.

## Usage

### Running the Web App

Ensure Ollama is running, then launch the Streamlit app:

```bash
streamlit run app.py
```

### Running Tests

To verify that all components are working correctly, run the test suite:

```bash
pytest -v
```