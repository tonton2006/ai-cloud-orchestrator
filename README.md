# GCP Cloud Orchestrator - MCP Server

A Model Context Protocol (MCP) server for managing Google Cloud Platform resources, including Compute Engine VMs and Cloud Run services.

## Overview

This MCP server provides tools for:

- **Compute Engine Management**: Start, stop, and list VM instances
- **Cloud Run Management**: Deploy, manage, and monitor Cloud Run services
- **Resource Aggregation**: View and search across all managed GCP resources

Built with FastMCP and deployable to Cloud Run with streamable HTTP transport.

## Project Structure

```
mcp_server/
├── __init__.py
├── main.py              # FastAPI + FastMCP entry point
├── config.py            # Pydantic settings configuration
├── tools/               # MCP tool implementations
│   ├── compute.py       # VM management
│   ├── cloudrun.py      # Cloud Run management
│   └── resources.py     # Aggregate resource listing
└── utils/               # Utility functions
    ├── gcp_auth.py      # GCP authentication helpers
    └── logger.py        # Logging configuration

tests/                   # Test suite
└── test_tools.py
```

## Prerequisites

- Python 3.12+
- Google Cloud Project with appropriate APIs enabled:
  - Compute Engine API
  - Cloud Run API
  - Resource Manager API
- GCP authentication configured (gcloud CLI or service account)

## Setup

### 1. Clone and Install

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your GCP project details
# Required: GCP_PROJECT_ID
# Optional: GCP_REGION, DEFAULT_ZONE, LOG_LEVEL
```

### 3. Authenticate with GCP

```bash
# Option 1: Use gcloud CLI (recommended for local development)
gcloud auth application-default login

# Option 2: Use service account key
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

## Running Locally

```bash
# Start the MCP server
python -m mcp_server.main

# Server runs on http://localhost:8080 with streamable HTTP transport
```

## Deploying to Cloud Run

```bash
# Build and deploy using the provided Dockerfile
gcloud run deploy gcp-orchestrator \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=your-project-id
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mcp_server --cov-report=html
```

### Code Formatting

```bash
# Format code with black
black mcp_server/ tests/

# Lint with ruff
ruff check mcp_server/ tests/

# Type checking with mypy
mypy mcp_server/
```

## Available Tools

### Compute Engine Tools

- `list_instances(zone)` - List all VM instances in a zone
- `start_instance(name, zone)` - Start a stopped VM instance
- `stop_instance(name, zone)` - Stop a running VM instance
- `get_instance_details(name, zone)` - Get detailed VM information

### Cloud Run Tools

- `list_services(region)` - List all Cloud Run services
- `deploy_service(name, image, region)` - Deploy or update a service
- `delete_service(name, region)` - Delete a Cloud Run service
- `get_service_details(name, region)` - Get service configuration
- `update_traffic(name, revisions, region)` - Update traffic allocation

### Resource Tools

- `list_all_resources()` - List all resources across services
- `get_resource_summary()` - Get resource usage summary
- `search_resources(query)` - Search resources by name/tag

## Configuration

Configuration is managed through environment variables (see `.env.example`):

- `GCP_PROJECT_ID` (required) - Your GCP project ID
- `GCP_REGION` - Default region for Cloud Run (default: us-central1)
- `DEFAULT_ZONE` - Default zone for Compute Engine (default: us-central1-a)
- `LOG_LEVEL` - Logging level (default: INFO)

## License

MIT

## Contributing

Contributions welcome! Please open an issue or submit a pull request.
