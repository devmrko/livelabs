# LiveLabs AI Assistant - Service Architecture

## Overview
The LiveLabs AI Assistant is a comprehensive system that provides personalized workshop recommendations through multi-step AI workflows, combining natural language processing, semantic search, and user skill progression tracking.

## Project Structure

```
livelabs/
├── MCP/                           # MCP Services (JSON-RPC & REST APIs)
│   ├── __init__.py
│   ├── mcp_config.json           # MCP server configuration
│   ├── mcp_livelabs_semantic_search.py      # MCP JSON-RPC interface
│   ├── mcp_livelabs_user_profiles.py        # MCP JSON-RPC interface
│   ├── mcp_livelabs_user_skills_progression.py  # MCP JSON-RPC interface
│   ├── rest_livelabs_nl_query.py            # REST API - NL to SQL
│   ├── rest_livelabs_semantic_search.py     # REST API - Vector search
│   ├── rest_livelabs_user_skills_progression.py  # REST API - Skills tracking
│   └── rest_livelabs_user_skills_progression_old.py  # Legacy version
├── utils/                         # Utility Modules
│   ├── __init__.py
│   ├── genai_client.py           # Oracle GenAI client
│   ├── mongo_utils.py            # MongoDB utilities
│   ├── oci_embedding.py          # OCI embedding service
│   ├── oracle_db.py              # Oracle database manager
│   └── vector_search.py          # Vector search engine
├── test/                          # Test Scripts
│   ├── test_batch_embedding.py
│   ├── test_direct_mcp.py
│   └── ...
├── logs/                          # Service logs (timestamped)
├── pids/                          # Process ID files
├── streamlit_livelabs_rest_app.py # Main Streamlit application
├── start_services.sh              # Service startup script
├── stop_services.sh               # Service shutdown script
├── requirements.txt               # Consolidated dependencies
└── README.md
```

## Core Services

### 1. Semantic Search Service (Port 8001)
**Files:** `MCP/rest_livelabs_semantic_search.py`, `MCP/mcp_livelabs_semantic_search.py`

- **Purpose**: Vector-based workshop search using embeddings
- **Technology**: Oracle Vector Database, Cohere embeddings
- **Key Features**:
  - Semantic similarity search across workshop content
  - COSINE distance calculations
  - Workshop metadata retrieval
  - Statistics and health monitoring

**API Endpoints:**
- `POST /search` - Semantic workshop search
- `GET /stats` - Search statistics
- `GET /health` - Service health check

### 2. Natural Language Query Service (Port 8002)
**Files:** `MCP/rest_livelabs_nl_query.py`

- **Purpose**: Convert natural language to SQL using Oracle SELECT AI
- **Technology**: Oracle SELECT AI, LLM prompt engineering
- **Key Features**:
  - User skill and history queries
  - Dynamic SQL generation
  - AI-driven query enhancement
  - Proper SQL escaping

**API Endpoints:**
- `POST /users/search/nl` - Natural language user queries
- `GET /health` - Service health check

### 3. User Skills Progression Service (Port 8003)
**Files:** `MCP/rest_livelabs_user_skills_progression.py`

- **Purpose**: Track user skills and workshop completions
- **Technology**: Oracle Database, MongoDB
- **Key Features**:
  - Skill level updates
  - Workshop completion tracking
  - Progress analytics
  - Dual database support

**API Endpoints:**
- `POST /users/{user_id}/skills` - Update user skills
- `POST /users/{user_id}/workshops/{workshop_id}/complete` - Mark completion
- `GET /health` - Service health check

### 4. Streamlit Frontend
**File:** `streamlit_livelabs_rest_app.py`

- **Purpose**: Web interface for multi-step AI workflows
- **Technology**: Streamlit, REST API integration
- **Key Features**:
  - Multi-step workflow execution
  - Real-time step visualization
  - Korean language output
  - API testing interface
  - Comprehensive logging

## Multi-Step Workflow

The system implements a sophisticated multi-step AI workflow:

1. **NL-to-SQL Step**: Extract user skills and workshop history
2. **Semantic Search Step**: Find relevant workshops based on context
3. **Skill Progression Step**: Update user progress
4. **AI Response Generation**: Create personalized recommendations in Korean

Each step builds upon previous results, creating a comprehensive context for final AI response generation.

## Service Management

### Startup
```bash
./start_services.sh
```
- Uses virtual environment (`venv/bin/python`)
- Detached execution with PID tracking
- Individual log files with timestamps
- Port conflict detection
- Service readiness verification

### Shutdown
```bash
./stop_services.sh
```
- Graceful shutdown (SIGTERM → SIGKILL)
- PID-based process management
- Port-based fallback detection
- Cleanup of PID files

### Monitoring
- **Logs**: `logs/` directory with timestamped files
- **PIDs**: `pids/` directory for process tracking
- **Health checks**: `/health` endpoints on all services

## Technology Stack

### Backend
- **Python 3.13** with virtual environment
- **FastAPI** for REST APIs
- **Oracle Database** for structured data
- **MongoDB** for document storage
- **Oracle GenAI** for LLM operations
- **Cohere** for embeddings

### Frontend
- **Streamlit** for web interface
- **Custom CSS** for styling
- **Real-time updates** and logging

### Infrastructure
- **MCP Protocol** for JSON-RPC services
- **REST APIs** for HTTP communication
- **Process management** with shell scripts
- **Logging** with Python logging module

## Configuration

### Environment Variables
- Oracle Database connection (OCI config)
- MongoDB connection strings
- API keys and credentials
- Service ports and endpoints

### Dependencies
All dependencies consolidated in `requirements.txt`:
- Web framework (FastAPI, Streamlit, uvicorn)
- Database clients (oracledb, pymongo)
- AI/ML libraries (Oracle GenAI, embeddings)
- MCP protocol support
- Utility libraries

## Development Guidelines

### Adding New Services
1. Create service file in `MCP/` directory
2. Follow naming convention: `rest_livelabs_*.py`
3. Add service to `start_services.sh` and `stop_services.sh`
4. Include health check endpoint
5. Add proper logging and error handling

### Import Structure
- Use `from utils.module_name import ClassName`
- Add project root to Python path for MCP services
- Maintain consistent import organization

### Testing
- Use `test/` directory for test scripts
- Test individual services and integration
- Verify health endpoints and API functionality

## Troubleshooting

### Common Issues
1. **Import errors**: Check Python path and module locations
2. **Port conflicts**: Use `lsof -i :PORT` to check usage
3. **Database connections**: Verify credentials and network access
4. **Service startup**: Check logs in `logs/` directory

### Log Analysis
- Service-specific logs with timestamps
- Structured logging with levels (INFO, ERROR, DEBUG)
- Request/response logging for API calls
- Error stack traces for debugging

## Future Enhancements

### Planned Features
- Enhanced error handling and retry logic
- Performance monitoring and metrics
- Automated testing and CI/CD
- Docker containerization
- Load balancing and scaling

### Architecture Improvements
- Service discovery mechanism
- Configuration management system
- Centralized logging and monitoring
- API versioning and documentation
- Security enhancements and authentication
