"""
Utility Functions Package

Contains helper functions for authentication, logging, and common operations.
"""

from .gcp_auth import get_compute_client, get_credentials
from .logger import get_logger

__all__ = ["get_compute_client", "get_credentials", "get_logger"]
