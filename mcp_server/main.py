"""
FastMCP Server Entry Point

This module sets up the MCP server with FastAPI and streamable HTTP transport.
"""

from fastmcp import FastMCP

from .config import settings
from .utils.logger import get_logger
from .tools import compute, cloudrun, resources, firewall

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
    ssh_public_key: str | None = None,
    ssh_username: str = "ubuntu",
):
    """
    Create a new Compute Engine VM instance with SSH access configured.

    IMPORTANT: For SSH access, you MUST provide an ssh_public_key. Ask the user for their SSH public key first:
    "To enable SSH access, I'll need your SSH public key. Can you run: cat ~/.ssh/id_rsa.pub (or id_ed25519.pub) and paste the result?"

    Args:
        instance_name: Name for the new instance
        zone: GCP zone where to create the instance. Defaults to configured default_zone.
        machine_type: Machine type for the instance (e.g., e2-micro, e2-medium, e2-standard-2). Defaults to e2-micro.
        image_family: OS image family to use (e.g., ubuntu-2204-lts, debian-12). Defaults to debian-12.
        image_project: Project containing the image (e.g., ubuntu-os-cloud, debian-cloud). Defaults to debian-cloud.
        disk_size_gb: Boot disk size in GB. Defaults to 10.
        ssh_public_key: SSH public key content (REQUIRED for SSH access). Format: 'ssh-rsa AAAA... user@host'
        ssh_username: Username for SSH login. Defaults to ubuntu.

    Returns:
        Operation details. Use get_instance_details(instance_name) to retrieve the external IP address after creation.
    """
    return await compute.create_instance(
        instance_name,
        zone,
        machine_type,
        image_family,
        image_project,
        disk_size_gb,
        ssh_public_key,
        ssh_username,
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


# Firewall tools
@mcp.tool()
async def create_firewall_rule(
    rule_name: str,
    ports: list[str],
    protocol: str = "tcp",
    source_ranges: list[str] | None = None,
    target_tags: list[str] | None = None,
    description: str | None = None
):
    """
    Create a firewall rule to allow incoming traffic.

    Common use cases:
    - Minecraft server: ports=["25565"], protocol="tcp"
    - Web server: ports=["80", "443"], protocol="tcp"
    - Custom app: ports=["8080"], protocol="tcp"

    Args:
        rule_name: Name for the firewall rule (e.g., "allow-minecraft")
        ports: List of ports to allow (e.g., ["25565", "80", "443"])
        protocol: Protocol to allow (tcp, udp, icmp). Defaults to tcp.
        source_ranges: Source IP ranges in CIDR notation. Defaults to ["0.0.0.0/0"] (allow all IPs).
        target_tags: Network tags to apply rule to (e.g., ["minecraft"]). If not specified, applies to all instances.
        description: Optional description for the rule

    Returns:
        Operation status and firewall rule details
    """
    return await firewall.create_firewall_rule(
        rule_name,
        ports,
        protocol,
        source_ranges,
        target_tags,
        description
    )


@mcp.tool()
async def delete_firewall_rule(rule_name: str):
    """
    Delete a firewall rule.

    Args:
        rule_name: Name of the firewall rule to delete

    Returns:
        Deletion status
    """
    return await firewall.delete_firewall_rule(rule_name)


@mcp.tool()
async def list_firewall_rules():
    """
    List all firewall rules in the project.

    Returns:
        List of firewall rules with their configurations (ports, protocols, source ranges, tags)
    """
    return await firewall.list_firewall_rules()


@mcp.tool()
async def add_tags_to_instance(
    instance_name: str,
    tags: list[str],
    zone: str | None = None
):
    """
    Add network tags to an instance to apply firewall rules.

    Network tags are used to selectively apply firewall rules to specific instances.
    For example, add tag "minecraft" to an instance, then create a firewall rule with target_tags=["minecraft"].

    Args:
        instance_name: Name of the instance
        tags: List of tags to add (e.g., ["minecraft", "web-server"])
        zone: GCP zone where the instance is located. Defaults to configured default_zone.

    Returns:
        Operation status with updated tag list
    """
    return await firewall.add_tags_to_instance(instance_name, tags, zone)


if __name__ == "__main__":
    logger.info(f"Starting MCP server for project: {settings.gcp_project_id}")

    # Run server with streamable HTTP transport on Cloud Run compatible settings
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8080)
