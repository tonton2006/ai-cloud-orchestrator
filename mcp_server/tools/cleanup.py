"""
Resource Cleanup Tools

Provides automated cleanup of expired GCP resources based on TTL labels.
"""

from typing import Dict, Any, List
from google.cloud import compute_v1

from ..config import settings
from ..utils.logger import get_logger
from ..utils.cleanup import should_cleanup_resource, format_cleanup_summary
from . import compute, cloudrun

logger = get_logger(__name__)


async def cleanup_expired_instances(
    zone: str | None = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Clean up expired Compute Engine VM instances based on TTL labels.

    Scans all instances in the specified zone for:
    - managed-by: mcp label
    - Expired TTL (based on created-at + ttl)

    Args:
        zone: GCP zone to scan. Defaults to settings.default_zone.
        dry_run: If True, only report what would be deleted without actually deleting.

    Returns:
        Cleanup summary with counts and lists of deleted/failed resources.
    """
    target_zone = zone or settings.default_zone
    logger.info(f"Starting cleanup of expired instances in zone: {target_zone} (dry_run={dry_run})")

    try:
        client = compute_v1.InstancesClient()
        instances = client.list(
            project=settings.gcp_project_id,
            zone=target_zone
        )

        total_scanned = 0
        total_expired = 0
        total_deleted = 0
        total_failed = 0
        deleted_resources = []
        failed_resources = []

        for instance in instances:
            total_scanned += 1
            instance_name = instance.name

            # Check if instance should be cleaned up
            should_cleanup, reason = should_cleanup_resource(
                instance_name,
                dict(instance.labels) if instance.labels else None
            )

            logger.debug(f"Instance {instance_name}: {reason}")

            if should_cleanup:
                total_expired += 1

                if dry_run:
                    logger.info(f"[DRY RUN] Would delete instance: {instance_name}")
                    deleted_resources.append(f"{instance_name} (dry-run)")
                    total_deleted += 1
                else:
                    # Actually delete the instance
                    logger.info(f"Deleting expired instance: {instance_name}")
                    try:
                        result = await compute.delete_instance(instance_name, target_zone)

                        if result.get("status") == "error":
                            logger.error(f"Failed to delete instance {instance_name}: {result.get('error')}")
                            failed_resources.append(f"{instance_name}: {result.get('error')}")
                            total_failed += 1
                        else:
                            logger.info(f"Successfully deleted instance: {instance_name}")
                            deleted_resources.append(instance_name)
                            total_deleted += 1

                    except Exception as e:
                        logger.error(f"Exception deleting instance {instance_name}: {str(e)}")
                        failed_resources.append(f"{instance_name}: {str(e)}")
                        total_failed += 1

        summary = format_cleanup_summary(
            total_scanned=total_scanned,
            total_expired=total_expired,
            total_deleted=total_deleted,
            total_failed=total_failed,
            deleted_resources=deleted_resources,
            failed_resources=failed_resources
        )

        summary["resource_type"] = "compute_instances"
        summary["zone"] = target_zone
        summary["dry_run"] = dry_run

        logger.info(f"Cleanup complete for instances in {target_zone}: {summary['message']}")
        return summary

    except Exception as e:
        logger.error(f"Failed to cleanup instances in {target_zone}: {str(e)}")
        return {
            "status": "error",
            "resource_type": "compute_instances",
            "zone": target_zone,
            "error": str(e),
            "message": f"Failed to cleanup instances: {str(e)}"
        }


async def cleanup_expired_services(
    region: str | None = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Clean up expired Cloud Run services based on TTL labels.

    Scans all services in the specified region for:
    - managed-by: mcp label
    - Expired TTL (based on created-at + ttl)

    Args:
        region: GCP region to scan. Defaults to settings.gcp_region.
        dry_run: If True, only report what would be deleted without actually deleting.

    Returns:
        Cleanup summary with counts and lists of deleted/failed resources.

    Note: This requires Cloud Run API implementation in cloudrun.py.
          Currently returns a placeholder until list_services() is fully implemented.
    """
    target_region = region or settings.gcp_region
    logger.info(f"Starting cleanup of expired Cloud Run services in region: {target_region} (dry_run={dry_run})")

    # TODO: Implement once cloudrun.list_services() is fully implemented
    # For now, return a placeholder response
    logger.warning("Cloud Run service cleanup not yet fully implemented (requires list_services implementation)")

    return {
        "status": "not_implemented",
        "resource_type": "cloud_run_services",
        "region": target_region,
        "dry_run": dry_run,
        "message": "Cloud Run service cleanup not yet implemented. Requires list_services() with label support.",
        "summary": {
            "total_scanned": 0,
            "total_expired": 0,
            "total_deleted": 0,
            "total_failed": 0,
            "success_rate": "N/A"
        },
        "deleted_resources": [],
        "failed_resources": []
    }


async def cleanup_all_expired_resources(
    zone: str | None = None,
    region: str | None = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Clean up all expired resources across Compute Engine and Cloud Run.

    This is a convenience function that calls both cleanup_expired_instances
    and cleanup_expired_services.

    Args:
        zone: GCP zone for Compute Engine instances. Defaults to settings.default_zone.
        region: GCP region for Cloud Run services. Defaults to settings.gcp_region.
        dry_run: If True, only report what would be deleted without actually deleting.

    Returns:
        Combined cleanup summary for all resource types.
    """
    logger.info(f"Starting cleanup of all expired resources (dry_run={dry_run})")

    # Cleanup Compute Engine instances
    instances_result = await cleanup_expired_instances(zone, dry_run)

    # Cleanup Cloud Run services
    services_result = await cleanup_expired_services(region, dry_run)

    # Combine results
    total_scanned = (
        instances_result.get("summary", {}).get("total_scanned", 0) +
        services_result.get("summary", {}).get("total_scanned", 0)
    )
    total_expired = (
        instances_result.get("summary", {}).get("total_expired", 0) +
        services_result.get("summary", {}).get("total_expired", 0)
    )
    total_deleted = (
        instances_result.get("summary", {}).get("total_deleted", 0) +
        services_result.get("summary", {}).get("total_deleted", 0)
    )
    total_failed = (
        instances_result.get("summary", {}).get("total_failed", 0) +
        services_result.get("summary", {}).get("total_failed", 0)
    )

    combined_result = {
        "status": "success",
        "dry_run": dry_run,
        "summary": {
            "total_scanned": total_scanned,
            "total_expired": total_expired,
            "total_deleted": total_deleted,
            "total_failed": total_failed,
            "success_rate": f"{(total_deleted / total_expired * 100):.1f}%" if total_expired > 0 else "N/A"
        },
        "by_resource_type": {
            "compute_instances": instances_result,
            "cloud_run_services": services_result
        },
        "message": f"Cleanup complete: {total_deleted} deleted, {total_failed} failed out of {total_expired} expired resources"
    }

    logger.info(f"All resource cleanup complete: {combined_result['message']}")
    return combined_result


async def list_expiring_resources(
    zone: str | None = None,
    days_until_expiration: int = 7
) -> Dict[str, Any]:
    """
    List resources that will expire within the specified number of days.

    Useful for getting advance warning before resources are automatically cleaned up.

    Args:
        zone: GCP zone to scan. Defaults to settings.default_zone.
        days_until_expiration: Number of days to look ahead (default: 7)

    Returns:
        List of resources expiring soon with their expiration dates.
    """
    from datetime import datetime, timezone, timedelta
    from ..utils.cleanup import parse_ttl, parse_created_at

    target_zone = zone or settings.default_zone
    logger.info(f"Listing resources expiring within {days_until_expiration} days in zone: {target_zone}")

    try:
        client = compute_v1.InstancesClient()
        instances = client.list(
            project=settings.gcp_project_id,
            zone=target_zone
        )

        current_time = datetime.now(timezone.utc)
        threshold_time = current_time + timedelta(days=days_until_expiration)

        expiring_soon = []
        permanent_resources = []

        for instance in instances:
            labels = dict(instance.labels) if instance.labels else {}

            if labels.get("managed-by") != "mcp":
                continue

            if "created-at" not in labels or "ttl" not in labels:
                continue

            ttl_str = labels["ttl"]
            if ttl_str.lower() == "never":
                permanent_resources.append({
                    "name": instance.name,
                    "zone": target_zone,
                    "ttl": "never",
                    "created_at": labels.get("created-at"),
                    "status": instance.status
                })
                continue

            try:
                created_at = parse_created_at(labels["created-at"])
                ttl_delta = parse_ttl(ttl_str)

                if ttl_delta:
                    expiration_time = created_at + ttl_delta

                    # Check if expires within threshold
                    if current_time <= expiration_time <= threshold_time:
                        days_until = (expiration_time - current_time).days
                        hours_until = ((expiration_time - current_time).seconds // 3600)

                        expiring_soon.append({
                            "name": instance.name,
                            "zone": target_zone,
                            "created_at": created_at.isoformat(),
                            "ttl": ttl_str,
                            "expires_at": expiration_time.isoformat(),
                            "days_until_expiration": days_until,
                            "hours_until_expiration": (days_until * 24) + hours_until,
                            "status": instance.status,
                            "owner": labels.get("owner", "unknown")
                        })

            except (ValueError, KeyError) as e:
                logger.warning(f"Failed to parse expiration for instance {instance.name}: {e}")
                continue

        # Sort by expiration time (soonest first)
        expiring_soon.sort(key=lambda x: x["expires_at"])

        return {
            "status": "success",
            "zone": target_zone,
            "days_threshold": days_until_expiration,
            "expiring_soon_count": len(expiring_soon),
            "permanent_count": len(permanent_resources),
            "expiring_soon": expiring_soon,
            "permanent_resources": permanent_resources,
            "message": f"Found {len(expiring_soon)} resources expiring within {days_until_expiration} days"
        }

    except Exception as e:
        logger.error(f"Failed to list expiring resources: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "message": f"Failed to list expiring resources: {str(e)}"
        }
