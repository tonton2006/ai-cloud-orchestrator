# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GCP Cloud Orchestrator is a Model Context Protocol (MCP) server built with FastMCP for managing Google Cloud Platform resources. It provides tools for Compute Engine VM management, Cloud Run service management, and cross-service resource aggregation. The server runs on FastAPI and is deployable to Cloud Run with streamable HTTP transport.

## Development Environment Setup

### Initial Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your GCP_PROJECT_ID (required)
```

### GCP Authentication
```bash
# For local development (recommended)
gcloud auth application-default login

# Or use service account
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

## Common Commands

### Running the Server
```bash
# Start MCP server locally on http://localhost:8080
python -m mcp_server.main
```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=mcp_server --cov-report=html

# Run specific test file
pytest tests/test_tools.py

# Run single test
pytest tests/test_tools.py::test_specific_function
```

### Code Quality
```bash
# Format code with black (required before committing)
black mcp_server/ tests/

# Lint with ruff
ruff check mcp_server/ tests/

# Type checking with mypy
mypy mcp_server/
```

### Deployment to Cloud Run
```bash
# Deploy using gcloud CLI
gcloud run deploy gcp-orchestrator \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=your-project-id
```

## Architecture

### Core Components

**FastMCP Integration** (`mcp_server/main.py`)
- Entry point that creates the FastMCP instance and registers all tools
- Each MCP tool is registered via `@mcp.tool()` decorator
- Tools are implemented as async functions and delegate to service modules
- Server runs with streamable HTTP transport on port 8080 for Cloud Run compatibility

**Configuration Management** (`mcp_server/config.py`)
- Pydantic Settings-based configuration loaded from environment variables
- Required: `GCP_PROJECT_ID`
- Optional: `GCP_REGION` (default: us-central1), `DEFAULT_ZONE` (default: us-central1-a), `LOG_LEVEL` (default: INFO)
- Reads from `.env` file for local development
- Global singleton `settings` instance is imported throughout the codebase

**Tool Modules** (`mcp_server/tools/`)
- `compute.py`: Compute Engine VM operations (list, start, stop, create, delete instances)
- `cloudrun.py`: Cloud Run service management (list, deploy, delete, traffic updates)
- `resources.py`: Aggregate resource listing and search across services
- Each module exports async functions that main.py wraps with @mcp.tool()

**Utilities** (`mcp_server/utils/`)
- `gcp_auth.py`: GCP authentication via Application Default Credentials (ADC), credential caching, client factory functions
- `logger.py`: Centralized logging with configurable levels, logger registry pattern

### Data Flow Pattern

1. MCP client calls tool via streamable HTTP transport
2. FastMCP routes to registered tool function in main.py
3. Tool function delegates to appropriate service module (compute/cloudrun/resources)
4. Service module uses GCP client from utils.gcp_auth
5. Service module returns structured dict/list response
6. FastMCP serializes and streams response back to client

### GCP Client Pattern

Tools use the google-cloud-* library clients (compute_v1, cloud run clients) authenticated via Application Default Credentials. The `get_credentials()` function in utils/gcp_auth.py caches credentials to avoid repeated authentication calls.

### Zone/Region Handling

All Compute Engine tools accept optional `zone` parameter (falls back to `settings.default_zone`). All Cloud Run tools accept optional `region` parameter (falls back to `settings.gcp_region`). This allows tools to work across multiple zones/regions while providing sensible defaults.

## Important Patterns

### Adding New MCP Tools

1. Create async function in appropriate service module (compute.py, cloudrun.py, or resources.py)
2. Add corresponding @mcp.tool() decorated function in main.py that calls your service function
3. Include comprehensive docstring - this becomes the tool's description in MCP
4. Return structured dict/list (not objects) for proper JSON serialization
5. Handle errors gracefully with try/except and return error status in response dict

### Error Handling Convention

Service functions return dict with status field:
```python
{
    "status": "success" | "pending" | "error",
    "message": "Human readable message",
    # ... other relevant fields
}
```

For errors, include `"error"` field with exception details. Tools should not raise exceptions to client - catch and return error status instead.

### Async Pattern

All tool functions are async. GCP clients are synchronous but wrapped in async functions for FastMCP compatibility. If adding blocking operations, consider running in executor.

### Testing Guidelines

- Mock GCP clients using pytest fixtures
- Test both success and error cases
- Verify correct project_id and zone/region are passed to clients
- Test default zone/region fallback behavior
- Use pytest-asyncio for async test functions

## SSH Access to VMs

### Phase 1: SSH Key Metadata (Current Implementation)

The `create_instance` tool now supports adding SSH public keys via VM metadata:

```python
create_instance(
    instance_name="my-vm",
    machine_type="e2-medium",
    ssh_public_key="ssh-rsa AAAA...your-public-key... user@host",
    ssh_username="ubuntu"
)
```

**How it works:**
- SSH public key is added to VM metadata during creation
- Key is associated with the specified username (default: ubuntu)
- VM becomes immediately accessible via SSH using the corresponding private key
- Works with the ssh-executor MCP server for end-to-end automation

**Getting your public key:**
```bash
cat ~/.ssh/id_rsa.pub  # or id_ed25519.pub
```

**Limitations (Phase 1):**
- Manual key management (must provide key for each VM)
- No centralized access control or audit trail
- Keys visible in VM metadata
- Not ideal for team environments

### Phase 2: OS Login (Production-Ready for Boomi)

**See TODO.md for Phase 2 implementation plan.**

OS Login will provide:
- IAM-based SSH access (no manual key management)
- Automatic key rotation via Google accounts
- Full audit trail in Cloud Logging
- Team-friendly access control
- 2FA/MFA support

**Priority:** Implement before Boomi team rollout

## Current Implementation Status

The project has a working skeleton with some tools fully implemented:
- `create_instance()` and `delete_instance()` in compute.py are fully implemented with SSH key metadata support
- Other compute tools (list, start, stop, get_instance_details) have TODO placeholders
- Cloud Run tools have placeholder implementations
- Resource aggregation tools need implementation

**Important:** `get_instance_details()` currently returns empty dict. Needs implementation to retrieve external IP addresses for SSH connection.

When implementing TODO items, follow the existing patterns in create_instance/delete_instance for client usage, error handling, and response structure.

## Docker and Cloud Run

The Dockerfile:
- Uses Python 3.12-slim for smaller image size
- Installs gcloud CLI (required for Cloud Run API operations)
- Creates non-root user for security
- Exposes port 8080 (Cloud Run standard)
- Includes health check endpoint
- Environment variables can be set via --set-env-vars in gcloud deploy

Cloud Run automatically provides service account credentials when deployed. No explicit credential configuration needed in production.
