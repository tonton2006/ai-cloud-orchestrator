"""
Compute Engine VM Management Tools

Provides MCP tools for managing Google Compute Engine virtual machines
using the google-cloud-compute library.
"""

from typing import List, Dict, Any
from google.cloud import compute_v1

from ..config import settings
from ..utils.logger import get_logger
from ..utils.gcp_auth import get_compute_client
from ..utils.labels import merge_labels

logger = get_logger(__name__)


# TODO: Import mcp instance from main.py to register tools
# from ..main import mcp


async def list_instances(zone: str | None = None) -> List[Dict[str, Any]]:
    """
    List all Compute Engine VM instances in the specified zone.

    Args:
        zone: GCP zone to list instances from. Defaults to settings.default_zone.

    Returns:
        List of instance details including name, status, machine type, and IP addresses.
    """
    target_zone = zone or settings.default_zone
    logger.info(f"Listing instances in zone: {target_zone}")

    try:
        client = compute_v1.InstancesClient()
        instances = client.list(
            project=settings.gcp_project_id,
            zone=target_zone
        )

        result = []
        for instance in instances:
            # Extract external IP
            external_ip = None
            internal_ip = None
            if instance.network_interfaces:
                network_interface = instance.network_interfaces[0]
                internal_ip = network_interface.network_i_p
                if network_interface.access_configs:
                    external_ip = network_interface.access_configs[0].nat_i_p

            # Extract machine type (just the type name)
            machine_type = instance.machine_type.split('/')[-1] if instance.machine_type else None

            result.append({
                "name": instance.name,
                "status": instance.status,
                "machine_type": machine_type,
                "zone": target_zone,
                "external_ip": external_ip,
                "internal_ip": internal_ip,
            })

        logger.info(f"Found {len(result)} instances in {target_zone}")
        return result

    except Exception as e:
        logger.error(f"Failed to list instances in {target_zone}: {str(e)}")
        return []


async def start_instance(instance_name: str, zone: str | None = None) -> Dict[str, str]:
    """
    Start a stopped Compute Engine VM instance.

    Args:
        instance_name: Name of the instance to start
        zone: GCP zone where the instance is located. Defaults to settings.default_zone.

    Returns:
        Operation status including operation ID and status message.
    """
    target_zone = zone or settings.default_zone
    logger.info(f"Starting instance {instance_name} in zone: {target_zone}")

    # TODO: Implement instance start using compute_v1.InstancesClient
    # client = get_compute_client()
    # operation = client.start(project=settings.gcp_project_id, zone=target_zone, instance=instance_name)

    return {"status": "pending", "message": f"Start operation initiated for {instance_name}"}


async def stop_instance(instance_name: str, zone: str | None = None) -> Dict[str, str]:
    """
    Stop a running Compute Engine VM instance.

    Args:
        instance_name: Name of the instance to stop
        zone: GCP zone where the instance is located. Defaults to settings.default_zone.

    Returns:
        Operation status including operation ID and status message.
    """
    target_zone = zone or settings.default_zone
    logger.info(f"Stopping instance {instance_name} in zone: {target_zone}")

    # TODO: Implement instance stop using compute_v1.InstancesClient
    # client = get_compute_client()
    # operation = client.stop(project=settings.gcp_project_id, zone=target_zone, instance=instance_name)

    return {"status": "pending", "message": f"Stop operation initiated for {instance_name}"}


async def get_instance_details(instance_name: str, zone: str | None = None) -> Dict[str, Any]:
    """
    Get detailed information about a specific Compute Engine VM instance.

    Args:
        instance_name: Name of the instance
        zone: GCP zone where the instance is located. Defaults to settings.default_zone.

    Returns:
        Detailed instance information including configuration, status, external IP, and metadata.
    """
    target_zone = zone or settings.default_zone
    logger.info(f"Getting details for instance {instance_name} in zone: {target_zone}")

    try:
        client = compute_v1.InstancesClient()
        instance = client.get(
            project=settings.gcp_project_id,
            zone=target_zone,
            instance=instance_name
        )

        # Extract external IP address
        external_ip = None
        internal_ip = None
        if instance.network_interfaces:
            network_interface = instance.network_interfaces[0]
            internal_ip = network_interface.network_i_p
            if network_interface.access_configs:
                external_ip = network_interface.access_configs[0].nat_i_p

        # Extract machine type (just the type name, not full path)
        machine_type = instance.machine_type.split('/')[-1] if instance.machine_type else None

        return {
            "name": instance.name,
            "status": instance.status,
            "machine_type": machine_type,
            "zone": target_zone,
            "external_ip": external_ip,
            "internal_ip": internal_ip,
            "disk_size_gb": instance.disks[0].disk_size_gb if instance.disks else None,
            "creation_timestamp": instance.creation_timestamp,
        }

    except Exception as e:
        logger.error(f"Failed to get instance details for {instance_name}: {str(e)}")
        return {
            "status": "error",
            "instance_name": instance_name,
            "error": str(e),
            "message": f"Failed to get instance details: {str(e)}"
        }


async def create_instance(
    instance_name: str,
    zone: str | None = None,
    machine_type: str = "e2-micro",
    image_family: str = "debian-12",
    image_project: str = "debian-cloud",
    disk_size_gb: int = 10,
    ssh_public_key: str | None = None,
    ssh_username: str = "ubuntu",
    enable_os_login: bool = True,
    labels: Dict[str, str] | None = None,
    ttl: str = "7d",
) -> Dict[str, Any]:
    """
    Create a new Compute Engine VM instance with automatic labeling for resource management.

    Args:
        instance_name: Name for the new instance
        zone: GCP zone where to create the instance. Defaults to settings.default_zone.
        machine_type: Machine type for the instance. Defaults to e2-micro.
        image_family: OS image family to use. Defaults to debian-12.
        image_project: Project containing the image. Defaults to debian-cloud.
        disk_size_gb: Boot disk size in GB. Defaults to 10.
        ssh_public_key: SSH public key content to add for access. Format: 'ssh-rsa AAAA... user@host'
                       Note: This is ignored when enable_os_login=True (OS Login manages keys automatically)
        ssh_username: Username for SSH access. Defaults to ubuntu.
                     Note: This is ignored when enable_os_login=True (OS Login uses IAM-based usernames)
        enable_os_login: Enable OS Login for IAM-based SSH access. Defaults to True.
                        When enabled, SSH access is managed via IAM roles instead of SSH key metadata.
        labels: Custom labels to add to the VM (optional). Will be merged with automatic labels.
        ttl: Time-to-live for auto-cleanup (e.g., "7d", "30d", "never"). Defaults to "7d".

    Returns:
        Operation details including operation ID, status, instance info, and external IP.

    Note: OS Login is the recommended approach for production use. It provides IAM-based access control,
          automatic key management, audit trails, and team-friendly access management.

    Auto-labeling: All VMs are automatically labeled with:
        - managed-by: "mcp" (indicates MCP-managed resource)
        - owner: "aglass1987-at-gmail-com" (owner email)
        - created-at: UTC timestamp (YYYYMMDD-HHMMSS)
        - ttl: Time-to-live for cleanup (configurable)
    """
    target_zone = zone or settings.default_zone
    logger.info(
        f"Creating instance {instance_name} in zone: {target_zone} "
        f"with machine type: {machine_type}"
    )

    # Merge user labels with default labels for auto-cleanup
    merged_labels = merge_labels(labels, ttl)
    logger.info(f"Applying labels to instance {instance_name}: {merged_labels}")

    try:
        client = compute_v1.InstancesClient()

        # Get the latest image from the specified family
        image_client = compute_v1.ImagesClient()
        image = image_client.get_from_family(
            project=image_project, family=image_family
        )

        # Configure the boot disk
        disk = compute_v1.AttachedDisk()
        disk.boot = True
        disk.auto_delete = True
        disk.initialize_params = compute_v1.AttachedDiskInitializeParams()
        disk.initialize_params.source_image = image.self_link
        disk.initialize_params.disk_size_gb = disk_size_gb

        # Configure network interface with external IP
        network_interface = compute_v1.NetworkInterface()
        network_interface.name = "global/networks/default"

        # Add access config for external IP
        access_config = compute_v1.AccessConfig()
        access_config.name = "External NAT"
        access_config.type_ = "ONE_TO_ONE_NAT"
        network_interface.access_configs = [access_config]

        # Create the instance configuration
        instance = compute_v1.Instance()
        instance.name = instance_name
        instance.machine_type = f"zones/{target_zone}/machineTypes/{machine_type}"
        instance.disks = [disk]
        instance.network_interfaces = [network_interface]

        # Apply labels for automatic resource management
        instance.labels = merged_labels

        # Configure metadata for SSH access
        metadata_items = []

        if enable_os_login:
            # Enable OS Login for IAM-based SSH access
            metadata_items.append(
                compute_v1.Items(
                    key="enable-oslogin",
                    value="TRUE"
                )
            )
            logger.info("OS Login enabled - SSH access will be managed via IAM roles")
        elif ssh_public_key:
            # Fallback to SSH key metadata (legacy approach)
            metadata_items.append(
                compute_v1.Items(
                    key="ssh-keys",
                    value=f"{ssh_username}:{ssh_public_key}"
                )
            )
            logger.info(f"SSH key metadata added for user: {ssh_username}")

        if metadata_items:
            metadata = compute_v1.Metadata()
            metadata.items = metadata_items
            instance.metadata = metadata

        # Create the instance
        operation = client.insert(
            project=settings.gcp_project_id,
            zone=target_zone,
            instance_resource=instance,
        )

        logger.info(
            f"Instance creation initiated: {instance_name}, operation: {operation.name}"
        )

        # Wait a moment for the instance to get an IP (optional - can be made async)
        # For now, return immediately and user can get IP with get_instance_details
        result = {
            "status": "pending",
            "operation_id": operation.name,
            "instance_name": instance_name,
            "zone": target_zone,
            "machine_type": machine_type,
            "message": f"Create operation initiated for {instance_name}",
        }

        if enable_os_login:
            result["os_login_enabled"] = True
            result["ssh_access_method"] = "IAM-based (OS Login)"
            result["note"] = "Use get_instance_details to retrieve the external IP. SSH access is managed via IAM roles."
        elif ssh_public_key:
            result["ssh_configured"] = True
            result["ssh_username"] = ssh_username
            result["ssh_access_method"] = "SSH key metadata"
            result["note"] = "Use get_instance_details to retrieve the external IP once the instance is running"

        return result

    except Exception as e:
        logger.error(f"Failed to create instance {instance_name}: {str(e)}")
        return {
            "status": "error",
            "instance_name": instance_name,
            "error": str(e),
            "message": f"Failed to create instance {instance_name}",
        }


async def delete_instance(
    instance_name: str, zone: str | None = None
) -> Dict[str, Any]:
    """
    Delete a Compute Engine VM instance.

    Args:
        instance_name: Name of the instance to delete
        zone: GCP zone where the instance is located. Defaults to settings.default_zone.

    Returns:
        Operation details including operation ID and status.
    """
    target_zone = zone or settings.default_zone
    logger.info(f"Deleting instance {instance_name} in zone: {target_zone}")

    try:
        client = compute_v1.InstancesClient()

        # Delete the instance
        operation = client.delete(
            project=settings.gcp_project_id,
            zone=target_zone,
            instance=instance_name,
        )

        logger.info(
            f"Instance deletion initiated: {instance_name}, operation: {operation.name}"
        )

        return {
            "status": "pending",
            "operation_id": operation.name,
            "instance_name": instance_name,
            "zone": target_zone,
            "message": f"Delete operation initiated for {instance_name}",
        }

    except Exception as e:
        logger.error(f"Failed to delete instance {instance_name}: {str(e)}")
        return {
            "status": "error",
            "instance_name": instance_name,
            "error": str(e),
            "message": f"Failed to delete instance {instance_name}",
        }
