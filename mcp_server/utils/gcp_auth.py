"""
GCP Authentication Helpers

Provides utilities for authenticating with Google Cloud Platform services.
"""

from typing import Optional
from google.auth import default
from google.auth.credentials import Credentials
from google.cloud import compute_v1

from ..config import settings
from .logger import get_logger

logger = get_logger(__name__)

# Cache for credentials
_cached_credentials: Optional[Credentials] = None


def get_credentials() -> Credentials:
    """
    Get GCP credentials using Application Default Credentials (ADC).

    This function will attempt to load credentials in the following order:
    1. GOOGLE_APPLICATION_CREDENTIALS environment variable
    2. gcloud CLI credentials
    3. Compute Engine/Cloud Run service account

    Returns:
        Credentials object for authenticating with GCP services.

    Raises:
        DefaultCredentialsError: If no valid credentials are found.
    """
    global _cached_credentials

    if _cached_credentials is None:
        logger.info("Loading GCP credentials using Application Default Credentials")

        # TODO: Implement credential loading
        # credentials, project = default()
        # _cached_credentials = credentials

        # Validate project matches configuration
        # if project != settings.gcp_project_id:
        #     logger.warning(
        #         f"Credential project ({project}) differs from configured project ({settings.gcp_project_id})"
        #     )

        # Placeholder
        credentials, project = default()
        _cached_credentials = credentials

    return _cached_credentials


def get_compute_client() -> compute_v1.InstancesClient:
    """
    Get authenticated Compute Engine client.

    Returns:
        InstancesClient configured with GCP credentials.
    """
    logger.debug("Creating Compute Engine client")

    # TODO: Implement client creation with proper credentials
    # credentials = get_credentials()
    # client = compute_v1.InstancesClient(credentials=credentials)

    client = compute_v1.InstancesClient()
    return client


def validate_project_access() -> bool:
    """
    Validate that the current credentials have access to the configured GCP project.

    Returns:
        True if access is valid, False otherwise.
    """
    logger.info(f"Validating access to project: {settings.gcp_project_id}")

    # TODO: Implement project access validation
    # Try to list resources or check project permissions
    # from google.cloud import resourcemanager_v3
    # client = resourcemanager_v3.ProjectsClient(credentials=get_credentials())
    # try:
    #     project = client.get_project(name=f"projects/{settings.gcp_project_id}")
    #     return True
    # except Exception as e:
    #     logger.error(f"Failed to access project: {e}")
    #     return False

    return True
