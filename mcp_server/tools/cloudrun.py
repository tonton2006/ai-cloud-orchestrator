"""
Cloud Run Service Management Tools

Provides MCP tools for managing Google Cloud Run services using gcloud CLI.
"""

import asyncio
import json
from typing import List, Dict, Any

from ..config import settings
from ..utils.logger import get_logger
from ..utils.labels import merge_labels

logger = get_logger(__name__)


async def list_services(region: str | None = None) -> List[Dict[str, Any]]:
    """
    List all Cloud Run services in the specified region.

    Args:
        region: GCP region to list services from. Defaults to settings.gcp_region.

    Returns:
        List of service details including name, URL, status, and configuration.
    """
    target_region = region or settings.gcp_region
    logger.info(f"Listing Cloud Run services in region: {target_region}")

    # TODO: Implement using gcloud CLI command
    # gcloud run services list --region={target_region} --project={settings.gcp_project_id} --format=json

    # Example command execution:
    # process = await asyncio.create_subprocess_exec(
    #     "gcloud", "run", "services", "list",
    #     "--region", target_region,
    #     "--project", settings.gcp_project_id,
    #     "--format", "json",
    #     stdout=asyncio.subprocess.PIPE,
    #     stderr=asyncio.subprocess.PIPE
    # )
    # stdout, stderr = await process.communicate()

    # Placeholder return
    return []


async def deploy_service(
    service_name: str,
    image: str,
    region: str | None = None,
    memory: str = "512Mi",
    cpu: str = "1",
    min_instances: int = 0,
    max_instances: int = 100,
    env_vars: Dict[str, str] | None = None,
    labels: Dict[str, str] | None = None,
    ttl: str = "7d",
) -> Dict[str, Any]:
    """
    Deploy a new Cloud Run service or update an existing one with automatic labeling.

    Args:
        service_name: Name of the Cloud Run service
        image: Container image URL (e.g., gcr.io/project/image:tag)
        region: GCP region for deployment. Defaults to settings.gcp_region.
        memory: Memory allocation for the service (e.g., "512Mi", "1Gi"). Defaults to "512Mi".
        cpu: CPU allocation for the service (e.g., "1", "2"). Defaults to "1".
        min_instances: Minimum number of instances to keep running. Defaults to 0.
        max_instances: Maximum number of instances to scale to. Defaults to 100.
        env_vars: Environment variables as key-value pairs. Defaults to None.
        labels: Custom labels to add to the service (optional). Will be merged with automatic labels.
        ttl: Time-to-live for auto-cleanup (e.g., "7d", "30d", "never"). Defaults to "7d".

    Returns:
        Deployment status and service URL.

    Auto-labeling: All Cloud Run services are automatically labeled with:
        - managed-by: "mcp" (indicates MCP-managed resource)
        - owner: "aglass1987-at-gmail-com" (owner email)
        - created-at: UTC timestamp (YYYYMMDD-HHMMSS)
        - ttl: Time-to-live for cleanup (configurable)
    """
    target_region = region or settings.gcp_region
    logger.info(f"Deploying Cloud Run service {service_name} in region: {target_region}")

    # Merge user labels with default labels for auto-cleanup
    merged_labels = merge_labels(labels, ttl)
    logger.info(f"Applying labels to service {service_name}: {merged_labels}")

    try:
        # Build gcloud run deploy command
        cmd = [
            "gcloud", "run", "deploy", service_name,
            "--image", image,
            "--region", target_region,
            "--project", settings.gcp_project_id,
            "--memory", memory,
            "--cpu", cpu,
            "--min-instances", str(min_instances),
            "--max-instances", str(max_instances),
            "--platform", "managed",
            "--allow-unauthenticated",
            "--quiet",  # Non-interactive mode
        ]

        # Add labels to the command
        # Format: --labels key1=value1,key2=value2
        label_pairs = [f"{key}={value}" for key, value in merged_labels.items()]
        label_string = ",".join(label_pairs)
        cmd.extend(["--labels", label_string])

        # Add environment variables if provided
        if env_vars:
            env_pairs = [f"{key}={value}" for key, value in env_vars.items()]
            for env_pair in env_pairs:
                cmd.extend(["--set-env-vars", env_pair])

        logger.info(f"Executing command: {' '.join(cmd)}")

        # Execute gcloud command using subprocess.exec (safe - no shell invocation)
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            logger.info(f"Successfully deployed Cloud Run service: {service_name}")

            # Parse output to extract service URL (gcloud outputs it in the response)
            output = stdout.decode()
            service_url = None

            # Look for "Service URL: https://..." in output
            for line in output.split('\n'):
                if "Service URL:" in line or "URL:" in line:
                    service_url = line.split(":", 1)[1].strip()
                    break

            return {
                "status": "success",
                "service_name": service_name,
                "region": target_region,
                "service_url": service_url,
                "message": f"Service {service_name} deployed successfully",
                "labels": merged_labels,
            }
        else:
            error_output = stderr.decode()
            logger.error(f"Failed to deploy Cloud Run service {service_name}: {error_output}")
            return {
                "status": "error",
                "service_name": service_name,
                "error": error_output,
                "message": f"Failed to deploy service {service_name}",
            }

    except Exception as e:
        logger.error(f"Exception while deploying Cloud Run service {service_name}: {str(e)}")
        return {
            "status": "error",
            "service_name": service_name,
            "error": str(e),
            "message": f"Failed to deploy service {service_name}",
        }


async def delete_service(service_name: str, region: str | None = None) -> Dict[str, str]:
    """
    Delete a Cloud Run service.

    Args:
        service_name: Name of the Cloud Run service to delete
        region: GCP region where the service is located. Defaults to settings.gcp_region.

    Returns:
        Deletion status message.
    """
    target_region = region or settings.gcp_region
    logger.info(f"Deleting Cloud Run service {service_name} in region: {target_region}")

    # TODO: Implement using gcloud CLI command
    # gcloud run services delete {service_name} --region={target_region} --project={settings.gcp_project_id} --quiet

    return {"status": "pending", "message": f"Deletion initiated for {service_name}"}


async def get_service_details(service_name: str, region: str | None = None) -> Dict[str, Any]:
    """
    Get detailed information about a specific Cloud Run service.

    Args:
        service_name: Name of the Cloud Run service
        region: GCP region where the service is located. Defaults to settings.gcp_region.

    Returns:
        Detailed service information including configuration, status, and URL.
    """
    target_region = region or settings.gcp_region
    logger.info(f"Getting details for Cloud Run service {service_name} in region: {target_region}")

    # TODO: Implement using gcloud CLI command
    # gcloud run services describe {service_name} --region={target_region} --project={settings.gcp_project_id} --format=json

    return {}


async def update_traffic(
    service_name: str,
    revisions: Dict[str, int],
    region: str | None = None
) -> Dict[str, str]:
    """
    Update traffic allocation between Cloud Run service revisions.

    Args:
        service_name: Name of the Cloud Run service
        revisions: Dictionary mapping revision names to traffic percentage
        region: GCP region where the service is located. Defaults to settings.gcp_region.

    Returns:
        Update status message.
    """
    target_region = region or settings.gcp_region
    logger.info(f"Updating traffic for Cloud Run service {service_name} in region: {target_region}")

    # TODO: Implement using gcloud CLI command
    # gcloud run services update-traffic {service_name} --region={target_region} --to-revisions=...

    return {"status": "pending", "message": f"Traffic update initiated for {service_name}"}
