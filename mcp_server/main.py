"""
FastMCP Server Entry Point

This module sets up the MCP server with FastAPI and streamable HTTP transport.
"""

from fastmcp import FastMCP

from .config import settings
from .utils.logger import get_logger
from .tools import compute, cloudrun, resources

# Initialize logger
logger = get_logger(__name__)

# Create FastMCP instance
mcp = FastMCP("gcp-cloud-orchestrator")


# Health check tool
@mcp.tool()
async def health_check() -> str:
    """
    Health check endpoint to verify the MCP server is running.

    Returns:
        str: Health status message
    """
    return "MCP Server is healthy"


# Compute Engine tools
@mcp.tool()
async def list_instances(zone: str | None = None):
    """
    List all Compute Engine VM instances in the specified zone.

    Args:
        zone: GCP zone to list instances from. Defaults to configured default_zone.

    Returns:
        List of instance details including name, status, machine type, and IP addresses.
    """
    return await compute.list_instances(zone)


@mcp.tool()
async def start_instance(instance_name: str, zone: str | None = None):
    """
    Start a stopped Compute Engine VM instance.

    Args:
        instance_name: Name of the instance to start
        zone: GCP zone where the instance is located. Defaults to configured default_zone.

    Returns:
        Operation status including operation ID and status message.
    """
    return await compute.start_instance(instance_name, zone)


@mcp.tool()
async def stop_instance(instance_name: str, zone: str | None = None):
    """
    Stop a running Compute Engine VM instance.

    Args:
        instance_name: Name of the instance to stop
        zone: GCP zone where the instance is located. Defaults to configured default_zone.

    Returns:
        Operation status including operation ID and status message.
    """
    return await compute.stop_instance(instance_name, zone)


@mcp.tool()
async def get_instance_details(instance_name: str, zone: str | None = None):
    """
    Get detailed information about a specific Compute Engine VM instance.

    Args:
        instance_name: Name of the instance
        zone: GCP zone where the instance is located. Defaults to configured default_zone.

    Returns:
        Detailed instance information including configuration, status, and metadata.
    """
    return await compute.get_instance_details(instance_name, zone)


@mcp.tool()
async def create_instance(
    instance_name: str,
    zone: str | None = None,
    machine_type: str = "e2-micro",
    image_family: str = "debian-12",
    image_project: str = "debian-cloud",
    disk_size_gb: int = 10,
):
    """
    Create a new Compute Engine VM instance.

    Args:
        instance_name: Name for the new instance
        zone: GCP zone where to create the instance. Defaults to configured default_zone.
        machine_type: Machine type for the instance. Defaults to e2-micro.
        image_family: OS image family to use. Defaults to debian-12.
        image_project: Project containing the image. Defaults to debian-cloud.
        disk_size_gb: Boot disk size in GB. Defaults to 10.

    Returns:
        Operation details including operation ID, status, and instance info.
    """
    return await compute.create_instance(
        instance_name,
        zone,
        machine_type,
        image_family,
        image_project,
        disk_size_gb,
    )


@mcp.tool()
async def delete_instance(instance_name: str, zone: str | None = None):
    """
    Delete a Compute Engine VM instance.

    Args:
        instance_name: Name of the instance to delete
        zone: GCP zone where the instance is located. Defaults to configured default_zone.

    Returns:
        Operation details including operation ID and status.
    """
    return await compute.delete_instance(instance_name, zone)


# Cloud Run tools
@mcp.tool()
async def list_services(region: str | None = None):
    """
    List all Cloud Run services in the specified region.

    Args:
        region: GCP region to list services from. Defaults to configured gcp_region.

    Returns:
        List of service details including name, URL, status, and configuration.
    """
    return await cloudrun.list_services(region)


@mcp.tool()
async def deploy_service(
    service_name: str,
    image: str,
    region: str | None = None,
    memory: str = "512Mi",
    cpu: str = "1",
    min_instances: int = 0,
    max_instances: int = 100,
    env_vars: dict | None = None
):
    """
    Deploy a new Cloud Run service or update an existing one.

    Args:
        service_name: Name of the Cloud Run service
        image: Container image URL (e.g., gcr.io/project/image:tag)
        region: GCP region for deployment. Defaults to configured gcp_region.
        memory: Memory allocation for the service (e.g., "512Mi", "1Gi"). Defaults to "512Mi".
        cpu: CPU allocation for the service (e.g., "1", "2"). Defaults to "1".
        min_instances: Minimum number of instances to keep running. Defaults to 0.
        max_instances: Maximum number of instances to scale to. Defaults to 100.
        env_vars: Environment variables as key-value pairs. Defaults to None.

    Returns:
        Deployment status and service URL.
    """
    return await cloudrun.deploy_service(
        service_name,
        image,
        region,
        memory=memory,
        cpu=cpu,
        min_instances=min_instances,
        max_instances=max_instances,
        env_vars=env_vars
    )


@mcp.tool()
async def delete_service(service_name: str, region: str | None = None):
    """
    Delete a Cloud Run service.

    Args:
        service_name: Name of the Cloud Run service to delete
        region: GCP region where the service is located. Defaults to configured gcp_region.

    Returns:
        Deletion status message.
    """
    return await cloudrun.delete_service(service_name, region)


@mcp.tool()
async def get_service_details(service_name: str, region: str | None = None):
    """
    Get detailed information about a specific Cloud Run service.

    Args:
        service_name: Name of the Cloud Run service
        region: GCP region where the service is located. Defaults to configured gcp_region.

    Returns:
        Detailed service information including configuration, status, and URL.
    """
    return await cloudrun.get_service_details(service_name, region)


@mcp.tool()
async def update_traffic(
    service_name: str,
    revisions: dict,
    region: str | None = None
):
    """
    Update traffic allocation between Cloud Run service revisions.

    Args:
        service_name: Name of the Cloud Run service
        revisions: Dictionary mapping revision names to traffic percentage
        region: GCP region where the service is located. Defaults to configured gcp_region.

    Returns:
        Update status message.
    """
    return await cloudrun.update_traffic(service_name, revisions, region)


# Aggregate resource tools
@mcp.tool()
async def list_all_resources():
    """
    List all managed GCP resources across Compute Engine and Cloud Run.

    Returns:
        Dictionary containing resources grouped by service type with summary counts.
    """
    return await resources.list_all_resources()


@mcp.tool()
async def get_resource_summary():
    """
    Get a high-level summary of GCP resource usage and costs.

    Returns:
        Summary including resource counts, running vs stopped instances,
        and estimated usage metrics.
    """
    return await resources.get_resource_summary()


@mcp.tool()
async def search_resources(query: str):
    """
    Search for GCP resources by name or tag across all services.

    Args:
        query: Search query string to match against resource names and tags

    Returns:
        List of matching resources with their type and key details.
    """
    return await resources.search_resources(query)


if __name__ == "__main__":
    logger.info(f"Starting MCP server for project: {settings.gcp_project_id}")

    # Run server with streamable HTTP transport on Cloud Run compatible settings
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8080)
