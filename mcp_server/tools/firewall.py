"""
Firewall Rule Management Tools

Provides MCP tools for managing GCP firewall rules.
"""

from typing import List, Dict, Any
from google.cloud import compute_v1

from ..config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


async def create_firewall_rule(
    rule_name: str,
    ports: List[str],
    protocol: str = "tcp",
    source_ranges: List[str] | None = None,
    target_tags: List[str] | None = None,
    description: str | None = None
) -> Dict[str, Any]:
    """
    Create a firewall rule to allow incoming traffic.

    Args:
        rule_name: Name for the firewall rule
        ports: List of ports to allow (e.g., ["25565", "80", "443"])
        protocol: Protocol to allow (tcp, udp, icmp). Defaults to tcp.
        source_ranges: Source IP ranges (CIDR notation). Defaults to ["0.0.0.0/0"] (allow all).
        target_tags: Network tags to apply rule to. If not specified, applies to all instances.
        description: Optional description for the rule

    Returns:
        Operation status and firewall rule details
    """
    if source_ranges is None:
        source_ranges = ["0.0.0.0/0"]  # Allow from anywhere by default

    logger.info(f"Creating firewall rule: {rule_name} for {protocol}:{','.join(ports)}")

    try:
        firewall_client = compute_v1.FirewallsClient()

        # Build the allowed configuration
        allowed = compute_v1.Allowed()
        allowed.I_p_protocol = protocol
        allowed.ports = ports

        # Create firewall rule resource
        firewall_rule = compute_v1.Firewall()
        firewall_rule.name = rule_name
        firewall_rule.direction = "INGRESS"
        firewall_rule.allowed = [allowed]
        firewall_rule.source_ranges = source_ranges
        firewall_rule.network = f"projects/{settings.gcp_project_id}/global/networks/default"

        if target_tags:
            firewall_rule.target_tags = target_tags

        if description:
            firewall_rule.description = description

        # Create the firewall rule
        operation = firewall_client.insert(
            project=settings.gcp_project_id,
            firewall_resource=firewall_rule
        )

        logger.info(f"Firewall rule creation initiated: {rule_name}")

        return {
            "status": "success",
            "rule_name": rule_name,
            "protocol": protocol,
            "ports": ports,
            "source_ranges": source_ranges,
            "target_tags": target_tags,
            "message": f"Firewall rule {rule_name} created successfully"
        }

    except Exception as e:
        logger.error(f"Failed to create firewall rule {rule_name}: {str(e)}")
        return {
            "status": "error",
            "rule_name": rule_name,
            "error": str(e),
            "message": f"Failed to create firewall rule: {str(e)}"
        }


async def delete_firewall_rule(rule_name: str) -> Dict[str, Any]:
    """
    Delete a firewall rule.

    Args:
        rule_name: Name of the firewall rule to delete

    Returns:
        Deletion status
    """
    logger.info(f"Deleting firewall rule: {rule_name}")

    try:
        firewall_client = compute_v1.FirewallsClient()

        operation = firewall_client.delete(
            project=settings.gcp_project_id,
            firewall=rule_name
        )

        logger.info(f"Firewall rule deletion initiated: {rule_name}")

        return {
            "status": "success",
            "rule_name": rule_name,
            "message": f"Firewall rule {rule_name} deleted successfully"
        }

    except Exception as e:
        logger.error(f"Failed to delete firewall rule {rule_name}: {str(e)}")
        return {
            "status": "error",
            "rule_name": rule_name,
            "error": str(e),
            "message": f"Failed to delete firewall rule: {str(e)}"
        }


async def list_firewall_rules() -> List[Dict[str, Any]]:
    """
    List all firewall rules in the project.

    Returns:
        List of firewall rules with their configurations
    """
    logger.info("Listing firewall rules")

    try:
        firewall_client = compute_v1.FirewallsClient()

        rules = firewall_client.list(project=settings.gcp_project_id)

        result = []
        for rule in rules:
            # Extract allowed protocols and ports
            allowed_list = []
            if rule.allowed:
                for allowed in rule.allowed:
                    allowed_list.append({
                        "protocol": allowed.I_p_protocol,
                        "ports": list(allowed.ports) if allowed.ports else []
                    })

            result.append({
                "name": rule.name,
                "direction": rule.direction,
                "allowed": allowed_list,
                "source_ranges": list(rule.source_ranges) if rule.source_ranges else [],
                "target_tags": list(rule.target_tags) if rule.target_tags else [],
                "description": rule.description if rule.description else ""
            })

        logger.info(f"Found {len(result)} firewall rules")
        return result

    except Exception as e:
        logger.error(f"Failed to list firewall rules: {str(e)}")
        return []


async def add_tags_to_instance(
    instance_name: str,
    tags: List[str],
    zone: str | None = None
) -> Dict[str, Any]:
    """
    Add network tags to an instance (used to apply firewall rules).

    Args:
        instance_name: Name of the instance
        tags: List of tags to add
        zone: GCP zone where the instance is located. Defaults to settings.default_zone.

    Returns:
        Operation status
    """
    target_zone = zone or settings.default_zone
    logger.info(f"Adding tags {tags} to instance {instance_name}")

    try:
        instances_client = compute_v1.InstancesClient()

        # Get current instance to retrieve existing tags and fingerprint
        instance = instances_client.get(
            project=settings.gcp_project_id,
            zone=target_zone,
            instance=instance_name
        )

        # Get existing tags
        existing_tags = list(instance.tags.items) if instance.tags and instance.tags.items else []

        # Merge new tags with existing (avoid duplicates)
        all_tags = list(set(existing_tags + tags))

        # Create tags resource with fingerprint
        tags_resource = compute_v1.Tags()
        tags_resource.items = all_tags
        tags_resource.fingerprint = instance.tags.fingerprint if instance.tags else None

        # Set tags on instance
        operation = instances_client.set_tags(
            project=settings.gcp_project_id,
            zone=target_zone,
            instance=instance_name,
            tags_resource=tags_resource
        )

        logger.info(f"Tags updated for instance {instance_name}")

        return {
            "status": "success",
            "instance_name": instance_name,
            "tags": all_tags,
            "message": f"Tags updated successfully for {instance_name}"
        }

    except Exception as e:
        logger.error(f"Failed to add tags to instance {instance_name}: {str(e)}")
        return {
            "status": "error",
            "instance_name": instance_name,
            "error": str(e),
            "message": f"Failed to add tags: {str(e)}"
        }
