"""
Resource Cleanup Utilities

Provides TTL parsing and expiration checking for automated resource cleanup.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Tuple
import re

from .logger import get_logger

logger = get_logger(__name__)


def parse_ttl(ttl: str) -> timedelta | None:
    """
    Parse a TTL string into a timedelta object.

    Args:
        ttl: Time-to-live string (e.g., "7d", "24h", "never")

    Returns:
        timedelta object or None if ttl is "never"

    Raises:
        ValueError: If TTL format is invalid

    Examples:
        >>> parse_ttl("7d")
        timedelta(days=7)
        >>> parse_ttl("24h")
        timedelta(hours=24)
        >>> parse_ttl("never")
        None
    """
    if ttl.lower() == "never":
        return None

    # Match pattern: number followed by d (days) or h (hours)
    match = re.match(r'^(\d+)([dh])$', ttl.lower())
    if not match:
        raise ValueError(f"Invalid TTL format: {ttl}. Expected format: '7d', '24h', or 'never'")

    value = int(match.group(1))
    unit = match.group(2)

    if unit == 'd':
        return timedelta(days=value)
    elif unit == 'h':
        return timedelta(hours=value)
    else:
        raise ValueError(f"Invalid TTL unit: {unit}. Expected 'd' or 'h'")


def parse_created_at(created_at: str) -> datetime:
    """
    Parse a created-at timestamp string into a datetime object.

    Args:
        created_at: Timestamp string in format "YYYYMMDD-HHMMSS"

    Returns:
        datetime object in UTC timezone

    Raises:
        ValueError: If timestamp format is invalid

    Examples:
        >>> parse_created_at("20250117-143000")
        datetime(2025, 1, 17, 14, 30, 0, tzinfo=timezone.utc)
    """
    try:
        # Parse format: YYYYMMDD-HHMMSS
        dt = datetime.strptime(created_at, "%Y%m%d-%H%M%S")
        # Make timezone-aware (UTC)
        return dt.replace(tzinfo=timezone.utc)
    except ValueError as e:
        raise ValueError(f"Invalid created-at format: {created_at}. Expected YYYYMMDD-HHMMSS") from e


def is_resource_expired(
    labels: Dict[str, str],
    current_time: datetime | None = None
) -> Tuple[bool, str]:
    """
    Check if a resource has exceeded its TTL and should be cleaned up.

    Args:
        labels: Resource labels containing 'created-at' and 'ttl'
        current_time: Current time (defaults to now in UTC, mainly for testing)

    Returns:
        Tuple of (is_expired: bool, reason: str)
        - is_expired: True if resource should be deleted
        - reason: Human-readable explanation

    Examples:
        >>> labels = {"created-at": "20250110-120000", "ttl": "7d"}
        >>> is_resource_expired(labels)
        (True, "Resource expired: created 2025-01-10 12:00:00+00:00, TTL 7d, age 7 days")
    """
    if current_time is None:
        current_time = datetime.now(timezone.utc)

    # Check if resource is MCP-managed
    if labels.get("managed-by") != "mcp":
        return False, "Not MCP-managed (missing 'managed-by: mcp' label)"

    # Check for required labels
    if "created-at" not in labels:
        logger.warning("Resource missing 'created-at' label, skipping cleanup")
        return False, "Missing 'created-at' label"

    if "ttl" not in labels:
        logger.warning("Resource missing 'ttl' label, skipping cleanup")
        return False, "Missing 'ttl' label"

    # Parse TTL
    try:
        ttl_delta = parse_ttl(labels["ttl"])
    except ValueError as e:
        logger.error(f"Invalid TTL format: {e}")
        return False, f"Invalid TTL format: {labels['ttl']}"

    # If TTL is "never", resource should not be cleaned up
    if ttl_delta is None:
        return False, "TTL is 'never' (permanent resource)"

    # Parse creation time
    try:
        created_at = parse_created_at(labels["created-at"])
    except ValueError as e:
        logger.error(f"Invalid created-at format: {e}")
        return False, f"Invalid created-at format: {labels['created-at']}"

    # Calculate expiration time
    expiration_time = created_at + ttl_delta
    age = current_time - created_at

    # Check if expired
    is_expired = current_time >= expiration_time

    if is_expired:
        reason = (
            f"Resource expired: created {created_at}, "
            f"TTL {labels['ttl']}, age {age.days} days {age.seconds // 3600} hours, "
            f"expired {(current_time - expiration_time).days} days ago"
        )
    else:
        time_remaining = expiration_time - current_time
        reason = (
            f"Resource not expired: created {created_at}, "
            f"TTL {labels['ttl']}, age {age.days} days {age.seconds // 3600} hours, "
            f"{time_remaining.days} days {time_remaining.seconds // 3600} hours remaining"
        )

    logger.debug(f"Expiration check: {reason}")
    return is_expired, reason


def should_cleanup_resource(
    resource_name: str,
    labels: Dict[str, str] | None,
    current_time: datetime | None = None
) -> Tuple[bool, str]:
    """
    Determine if a resource should be cleaned up (convenience wrapper).

    Args:
        resource_name: Name of the resource (for logging)
        labels: Resource labels (can be None)
        current_time: Current time (defaults to now in UTC)

    Returns:
        Tuple of (should_cleanup: bool, reason: str)
    """
    if labels is None:
        return False, f"{resource_name}: No labels found"

    is_expired, reason = is_resource_expired(labels, current_time)
    return is_expired, f"{resource_name}: {reason}"


def format_cleanup_summary(
    total_scanned: int,
    total_expired: int,
    total_deleted: int,
    total_failed: int,
    deleted_resources: list[str],
    failed_resources: list[str]
) -> Dict[str, Any]:
    """
    Format a cleanup operation summary.

    Args:
        total_scanned: Total number of resources scanned
        total_expired: Number of expired resources found
        total_deleted: Number of resources successfully deleted
        total_failed: Number of deletion failures
        deleted_resources: List of deleted resource names
        failed_resources: List of failed resource names

    Returns:
        Dictionary containing cleanup summary
    """
    return {
        "summary": {
            "total_scanned": total_scanned,
            "total_expired": total_expired,
            "total_deleted": total_deleted,
            "total_failed": total_failed,
            "success_rate": f"{(total_deleted / total_expired * 100):.1f}%" if total_expired > 0 else "N/A"
        },
        "deleted_resources": deleted_resources,
        "failed_resources": failed_resources,
        "message": f"Cleanup complete: {total_deleted} deleted, {total_failed} failed out of {total_expired} expired resources"
    }
