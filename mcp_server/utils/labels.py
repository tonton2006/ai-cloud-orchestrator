"""
Resource Labeling Utilities

Provides automatic labeling for GCP resources to support automated cleanup.
Labels include: managed-by, owner, created-at, and ttl (time-to-live).
"""

from datetime import datetime, timezone
from typing import Dict

from .logger import get_logger

logger = get_logger(__name__)


def get_default_labels() -> Dict[str, str]:
    """
    Generate default labels for GCP resource creation.

    Returns:
        Dictionary containing default labels:
        - managed-by: "mcp" (indicates resource is MCP-managed)
        - owner: "aglass1987-at-gmail-com" (owner email, sanitized for GCP)
        - created-at: UTC timestamp in format YYYYMMDD-HHMMSS
        - ttl: "7d" (default time-to-live of 7 days)

    Note: GCP labels have strict requirements:
    - Keys and values must be lowercase
    - No special characters except hyphens
    - Max 63 characters per key/value
    - @ and . are converted to hyphens
    """
    # Generate UTC timestamp for created-at label
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%d-%H%M%S")

    # Owner email sanitized for GCP label format
    # GCP labels don't allow @ or . characters
    owner_email = "aglass1987-at-gmail-com"

    labels = {
        "managed-by": "mcp",
        "owner": owner_email,
        "created-at": timestamp,
        "ttl": "7d",
    }

    logger.debug(f"Generated default labels: {labels}")
    return labels


def merge_labels(user_labels: Dict[str, str] | None, ttl: str = "7d") -> Dict[str, str]:
    """
    Merge user-provided labels with default system labels.

    User labels take precedence over default labels (except managed-by and created-at).
    The ttl parameter overrides the default ttl value.

    Args:
        user_labels: Optional dictionary of user-provided labels
        ttl: Time-to-live for auto-cleanup (e.g., "7d", "30d", "never"). Defaults to "7d".

    Returns:
        Merged dictionary of labels with defaults + user overrides

    Example:
        >>> merge_labels({"env": "prod", "team": "platform"}, ttl="30d")
        {
            "managed-by": "mcp",
            "owner": "aglass1987-at-gmail-com",
            "created-at": "20250117-143000",
            "ttl": "30d",
            "env": "prod",
            "team": "platform"
        }

    Note: GCP has a limit of 64 labels per resource. This function does not enforce
    that limit - validation happens at the GCP API level.
    """
    # Start with default labels
    merged = get_default_labels()

    # Override TTL if specified
    if ttl:
        merged["ttl"] = ttl

    # Merge user labels (user labels can override owner and ttl, but not managed-by or created-at)
    if user_labels:
        # Validate and sanitize user labels
        sanitized_user_labels = {}
        for key, value in user_labels.items():
            # Convert to lowercase and replace invalid characters
            sanitized_key = key.lower().replace("_", "-").replace(".", "-").replace("@", "-")
            sanitized_value = str(value).lower().replace("_", "-").replace(".", "-").replace("@", "-")

            # Truncate if too long (GCP max is 63 characters)
            sanitized_key = sanitized_key[:63]
            sanitized_value = sanitized_value[:63]

            sanitized_user_labels[sanitized_key] = sanitized_value

        # Apply user labels (except managed-by and created-at which are immutable)
        for key, value in sanitized_user_labels.items():
            if key not in ["managed-by", "created-at"]:
                merged[key] = value

        logger.debug(f"Merged user labels: {sanitized_user_labels}")

    logger.info(f"Final labels for resource: {merged}")
    return merged


def validate_ttl(ttl: str) -> bool:
    """
    Validate that a TTL string follows the expected format.

    Valid formats:
    - "Xd" for X days (e.g., "7d", "30d")
    - "Xh" for X hours (e.g., "24h", "72h")
    - "never" for no automatic cleanup

    Args:
        ttl: Time-to-live string to validate

    Returns:
        True if valid, False otherwise

    Example:
        >>> validate_ttl("7d")
        True
        >>> validate_ttl("never")
        True
        >>> validate_ttl("invalid")
        False
    """
    if ttl == "never":
        return True

    if len(ttl) < 2:
        return False

    # Check if format is Xd or Xh
    unit = ttl[-1]
    if unit not in ["d", "h"]:
        return False

    # Check if the numeric part is valid
    try:
        int(ttl[:-1])
        return True
    except ValueError:
        return False
