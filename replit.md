# AI Task & Delegation Manager

## Overview

This is a Streamlit-based AI-powered task and delegation management application designed for tech leadership. The application leverages OpenAI's GPT-4o model to automatically extract action items from meeting notes and text, then provides comprehensive task management, delegation tracking, and timeline visualization capabilities.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application follows a modular architecture with clear separation of concerns across multiple components:

### Frontend Architecture
- **Streamlit Framework**: Web-based interface with multi-page navigation
- **Interactive Visualizations**: Plotly-based charts and graphs for data visualization
- **Session State Management**: Streamlit session state for maintaining application state across user interactions

### Backend Architecture
- **Modular Python Classes**: Each major functionality is encapsulated in dedicated classes
- **API Integration**: OpenAI API integration for AI-powered action item extraction
- **File-based Data Storage**: JSON files for persistent data storage

## Key Components

### 1. AI Processing (`ai_processor.py`)
- **Purpose**: Extracts action items from meeting notes using configurable AI backends
- **Features**: Auto-categorization, auto-delegation suggestions, priority assessment
- **Backends**: Supports Perplexity Pro API, Ollama (local), and OpenAI
- **Fallback**: Includes fallback extraction methods when AI is unavailable
- **Default Model**: llama-3.1-sonar-small-128k-online (Perplexity) or llama3.1:8b (Ollama)

### 2. Task Management (`task_manager.py`)
- **Purpose**: Handles core task management logic
- **Features**: Urgency scoring algorithm, priority weighting, task categorization
- **Scoring System**: Combines due date urgency (40%), priority (40%), and category importance (10%)

### 3. Data Handling (`data_handler.py` + `database.py`)
- **Purpose**: Manages data persistence and retrieval with SQLite database
- **Storage**: Local SQLite database (`data/tasks.db`) with automatic migration from JSON
- **Tables**: Separate tables for tasks, delegations, and settings with proper relationships
- **Migration**: Automatic migration from existing JSON files to database on first run
- **Backup**: Database backup functionality with versioned backup files

### 4. Visualization (`visualization.py`)
- **Purpose**: Creates interactive charts and timeline visualizations
- **Charts**: Gantt charts, priority distributions, progress tracking
- **Styling**: Consistent color schemes for priorities and task statuses

### 5. Utilities (`utils.py`)
- **Purpose**: Shared utility functions
- **Features**: Date formatting, relative date calculations, priority color mapping

### 6. Main Application (`app.py`)
- **Purpose**: Streamlit application entry point and UI orchestration
- **Pages**: Multi-page interface with dashboard, extraction, management, and analytics views
- **State Management**: Initializes and manages session state for all components

## Data Flow

1. **Input**: User provides meeting notes or text through the Streamlit interface
2. **AI Processing**: Text is sent to OpenAI API for action item extraction
3. **Task Creation**: Extracted items are converted to structured task objects
4. **Storage**: Tasks are saved to JSON files via DataHandler
5. **Visualization**: Tasks are processed and displayed through various charts and views
6. **Management**: Users can edit, delegate, and track task progress

## External Dependencies

### Core Dependencies
- **Streamlit**: Web application framework
- **Perplexity Pro**: AI processing for action item extraction
- **Plotly**: Interactive data visualization
- **Pandas**: Data manipulation and analysis
- **Requests**: HTTP library for API communication

### AI Backend Dependencies
- **Perplexity Pro API**: Cloud-based AI processing (requires PERPLEXITY_API_KEY)
- **Ollama**: Local LLM processing (requires local Ollama installation)
- **OpenAI API**: Cloud-based AI processing (requires OPENAI_API_KEY)
- **Environment Variables**: Backend-specific API keys and configuration

### Data Dependencies
- **SQLite Database**: Local SQLite database for persistent data storage
- **SQLAlchemy ORM**: Object-relational mapping for database operations
- **Migration System**: Automatic migration from legacy JSON files to database
- **Directory Structure**: `/data` folder for database file and backups

## Deployment Strategy

### Development Environment
- **Local Development**: Designed to run locally with Streamlit
- **Configuration**: Environment variables for API keys
- **Data Persistence**: File-based storage suitable for single-user deployment

### Production Considerations
- **Scalability**: Current architecture supports single-user deployments
- **Data Storage**: Could be migrated to database systems for multi-user scenarios
- **API Management**: Includes fallback mechanisms for API unavailability
- **Security**: API keys managed through environment variables

### Key Architectural Decisions

1. **File-based Storage**: Chosen for simplicity and single-user focus, with easy migration path to databases
2. **Modular Design**: Each component is independent, allowing for easy testing and maintenance
3. **Flexible AI Integration**: Multi-backend AI support (Perplexity, Ollama, OpenAI) provides choice between cloud and local processing
4. **Local AI Support**: Ollama integration enables privacy-focused, offline AI processing without external API dependencies
5. **Fallback Mechanisms**: Application remains functional even when AI services are unavailable
6. **Session State Management**: Streamlit's session state provides seamless user experience across page navigation

The architecture prioritizes ease of use, modularity, and extensibility while maintaining a focus on tech leadership use cases.