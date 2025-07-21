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
- **Purpose**: Extracts action items from meeting notes using Perplexity Pro API
- **Features**: Auto-categorization, auto-delegation suggestions, priority assessment
- **Fallback**: Includes fallback extraction methods when API is unavailable
- **Model**: Configured to use llama-3.1-sonar-small-128k-online by default

### 2. Task Management (`task_manager.py`)
- **Purpose**: Handles core task management logic
- **Features**: Urgency scoring algorithm, priority weighting, task categorization
- **Scoring System**: Combines due date urgency (40%), priority (40%), and category importance (10%)

### 3. Data Handling (`data_handler.py`)
- **Purpose**: Manages data persistence and retrieval
- **Storage**: JSON files in `/data` directory
- **Files**: Separate files for tasks, delegations, and settings
- **Versioning**: Includes data versioning and timestamp tracking

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

### API Dependencies
- **Perplexity Pro API**: Required for AI-powered action item extraction
- **Environment Variables**: PERPLEXITY_API_KEY for API authentication

### Data Dependencies
- **JSON Files**: Local file system for data persistence
- **Directory Structure**: `/data` folder for organized file storage

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
3. **AI Integration**: OpenAI API provides advanced natural language processing capabilities
4. **Fallback Mechanisms**: Application remains functional even when AI services are unavailable
5. **Session State Management**: Streamlit's session state provides seamless user experience across page navigation

The architecture prioritizes ease of use, modularity, and extensibility while maintaining a focus on tech leadership use cases.