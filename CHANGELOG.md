# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2025-07-25

This is the initial stable release of the Task Master AI.

### Features

-   **Agentic Core**: Implemented a core agent using LangGraph to process inputs.
-   **Tool Integration**: Added tools for natural date parsing (`parsedatetime`) and web search (`tavily`).
-   **File Handling**: Added support for reading `.txt`, `.docx`, and `.pdf` files.
-   **Streamlit UI**: Built a user-friendly interface with tabs for text input and file uploads.
-   **Rules Engine**: Created a configurable engine using `config.yaml` to apply custom priorities to tasks.
-   **Structured Output**: Shifted the agent to produce reliable JSON output for easier parsing.
-   **Configuration**: Centralized model configuration using a `.env` file.
-   **Logging**: Implemented structured logging to both the console and `app.log`.
-   **Testing**: Developed a suite of unit tests with `pytest` for core components.
-   **Project Structure**: Set up a scalable project structure with `pyproject.toml`.