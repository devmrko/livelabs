# LiveLabs Workshop MCP Services

This project provides three separate MCP (Model Context Protocol) services for LiveLabs workshop management:

1. **LiveLabs Data Retrieval Service** - Data retrieval and batch processing for LiveLabs workshops from MongoDB
2. **LiveLabs Semantic Search Service** - Semantic search using vector similarity for LiveLabs workshops
3. **Oracle SELECT AI Service** - Natural language database queries

## Installation

1. Install MCP dependencies:
```bash
pip install -r requirements_mcp.txt
```

2. Ensure your `.env` file is configured with database credentials:
```env
# Oracle Database
DB_USER=your_username
DB_PASSWORD=your_password
DB_DSN=your_database_connection_string
WALLET_LOCATION=/path/to/wallet/directory
TNS_ADMIN=/path/to/tns/admin/directory
PEM_PASSPHRASE=your_wallet_password_if_encrypted

# MongoDB
MONGO_USER=your_mongo_user
MONGO_PASSWORD=your_mongo_password
MONGO_HOST=your_mongo_host
MONGO_PORT=27017

# OCI Configuration
OCI_CONFIG_PATH=/path/to/oci/config
OCI_KEY_PATH=/path/to/oci/key
```

## Available MCP Services

### 1. LiveLabs Data Retrieval Service (`mcp_livelabs_data_retrieval.py`)

**Purpose**: Retrieves LiveLabs workshop data from MongoDB, generates embeddings, and updates Oracle database.

#### Tools:
- **`process_livelabs_workshops`**: Process LiveLabs workshops from MongoDB
  - `limit` (optional): Number of LiveLabs workshops to process
  - `collection_name` (optional): MongoDB collection name containing LiveLabs workshops (default: "livelabs_workshops_json2")

- **`get_livelabs_processing_status`**: Get status and statistics of the last LiveLabs workshop processing job

- **`get_livelabs_workshop_count`**: Get the count of LiveLabs workshops available for processing
  - `collection_name` (optional): MongoDB collection name to count from (default: "livelabs_workshops_json2")

#### Example:
```json
{
  "name": "process_livelabs_workshops",
  "arguments": {
    "limit": 50,
    "collection_name": "livelabs_workshops_json2"
  }
}
```

### 2. LiveLabs Semantic Search Service (`mcp_livelabs_semantic_search.py`)

**Purpose**: Semantic search using vector similarity specifically for LiveLabs workshops.

#### Tools:
- **`search_livelabs_workshops`**: Search LiveLabs workshops using semantic similarity
  - `query` (required): Natural language search query for LiveLabs workshops
  - `top_k` (optional): Number of LiveLabs workshop results to return (default: 10)
  - `similarity_threshold` (optional): Minimum similarity threshold (0.0 to 1.0)

- **`get_livelabs_statistics`**: Get statistics about LiveLabs workshops in the database

- **`find_similar_livelabs_workshops`**: Find LiveLabs workshops similar to a specific workshop by ID
  - `workshop_id` (required): LiveLabs workshop ID to find similar workshops for
  - `top_k` (optional): Number of similar LiveLabs workshops to return (default: 5)

#### Example:
```json
{
  "name": "search_livelabs_workshops",
  "arguments": {
    "query": "big data service",
    "top_k": 5,
    "similarity_threshold": 0.7
  }
}
```

### 3. Oracle SELECT AI Service (`mcp_select_ai.py`)

**Purpose**: Query Oracle database using natural language with SELECT AI.

#### Tools:
- **`query_with_select_ai`**: Query database using natural language
  - `query` (required): Natural language query
  - `profile_name` (optional): AI profile name (default: "DISCOVERYDAY_AI_PROFILE")

- **`set_ai_profile`**: Set the AI profile for SELECT AI queries
  - `profile_name` (required): AI profile name to set

- **`run_example_queries`**: Run predefined example queries
  - `example_type` (optional): Type of examples ('basic', 'advanced', 'all')

- **`get_connection_status`**: Check connection status to Oracle database

#### Example:
```json
{
  "name": "query_with_select_ai",
  "arguments": {
    "query": "what kinds of skill John Smith have, and how good are those",
    "profile_name": "DISCOVERYDAY_AI_PROFILE"
  }
}
```

## Usage

### Running Individual MCP Servers

1. **LiveLabs Data Retrieval Service**:
```bash
python mcp_livelabs_data_retrieval.py
```

2. **LiveLabs Semantic Search Service**:
```bash
python mcp_livelabs_semantic_search.py
```

3. **Oracle SELECT AI Service**:
```bash
python mcp_select_ai.py
```

### Integration with MCP Clients

Add the following to your MCP client configuration:

```json
{
  "mcpServers": {
    "livelabs-data-retrieval-service": {
      "command": "python",
      "args": ["mcp_livelabs_data_retrieval.py"],
      "env": {
        "PYTHONPATH": "."
      }
    },
    "livelabs-semantic-search-service": {
      "command": "python",
      "args": ["mcp_livelabs_semantic_search.py"],
      "env": {
        "PYTHONPATH": "."
      }
    },
    "oracle-select-ai-service": {
      "command": "python",
      "args": ["mcp_select_ai.py"],
      "env": {
        "PYTHONPATH": "."
      }
    }
  }
}
```

### Example Workflows

#### 1. Complete LiveLabs Workshop Processing Pipeline
```json
[
  {
    "name": "get_livelabs_workshop_count",
    "arguments": {}
  },
  {
    "name": "process_livelabs_workshops",
    "arguments": {"limit": 100}
  },
  {
    "name": "get_livelabs_processing_status",
    "arguments": {}
  }
]
```

#### 2. LiveLabs Workshop Search and Analysis
```json
[
  {
    "name": "search_livelabs_workshops",
    "arguments": {
      "query": "machine learning",
      "top_k": 10
    }
  },
  {
    "name": "query_with_select_ai",
    "arguments": {
      "query": "what are the most popular machine learning workshops"
    }
  }
]
```

#### 3. Advanced LiveLabs Analysis Workflow
```json
[
  {
    "name": "run_example_queries",
    "arguments": {"example_type": "advanced"}
  },
  {
    "name": "find_similar_livelabs_workshops",
    "arguments": {
      "workshop_id": "workshop_123",
      "top_k": 5
    }
  }
]
```

## Service Architecture

Each MCP service is designed to be:

- **Independent**: Can run separately without dependencies on other services
- **Focused**: Each service has a specific purpose and set of tools
- **Scalable**: Can be deployed independently based on usage patterns
- **Maintainable**: Clear separation of concerns and responsibilities

### Service Responsibilities:

1. **LiveLabs Data Retrieval Service**:
   - LiveLabs workshop data retrieval from MongoDB
   - OCI embedding generation for LiveLabs workshops
   - Oracle database updates with LiveLabs workshop embeddings
   - LiveLabs workshop processing statistics

2. **LiveLabs Semantic Search Service**:
   - LiveLabs-specific vector similarity calculations
   - Natural language query processing for LiveLabs workshops
   - LiveLabs workshop statistics and analytics
   - Similar LiveLabs workshop recommendations

3. **Oracle SELECT AI Service**:
   - Oracle SELECT AI integration
   - Natural language query processing
   - AI profile management
   - Example query demonstrations

## Features

- **Modular Design**: Each service can be used independently
- **LiveLabs-Specific**: All services are specifically designed for LiveLabs workshop management
- **Comprehensive Error Handling**: Detailed error messages and logging
- **Connection Management**: Efficient database connection pooling
- **Flexible Configuration**: Environment-based configuration
- **Rich Tool Schemas**: Detailed input validation and documentation
- **Status Monitoring**: Connection and service health checks

## Troubleshooting

### Common Issues

1. **Connection Errors**: Ensure your `.env` file is properly configured
2. **MCP Dependencies**: Make sure `mcp>=1.0.0` is installed
3. **Database Permissions**: Verify database user has necessary permissions
4. **OCI Configuration**: Ensure OCI config and key files are accessible

### Service-Specific Issues

- **LiveLabs Data Retrieval Service**: Check MongoDB connection and LiveLabs collection access
- **LiveLabs Semantic Search Service**: Verify Oracle vector column exists and has LiveLabs workshop data
- **Oracle SELECT AI Service**: Ensure AI profile is configured in Oracle

### Logging

Each service provides detailed logging:
- Connection initialization
- Tool execution
- Error details
- Performance metrics

## Security

- Database credentials are loaded from environment variables
- No sensitive data is logged
- Connections are properly closed after use
- Input validation is performed on all parameters
- Each service has isolated connection management
