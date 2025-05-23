import logging
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple


@dataclass
class ReleaseInfo:
    """Release information for a specific version"""

    version: str
    release_date: Optional[str] = None
    prerelease: bool = False
    additional_info: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Post-initialization method to clean and standardize version info."""
        self.version = clean_version(self.version)
        self.release_date = standardize_date(self.release_date)

        # Ensure prerelease flag is consistent with version string
        if not self.prerelease:
            self.prerelease = is_prerelease(self.version)

    def __eq__(self, other: Any) -> bool:
        """Equality comparison based on version and prerelease status."""
        if not isinstance(other, ReleaseInfo):
            return NotImplemented
        return self.version == other.version and self.prerelease == other.prerelease

    def __ne__(self, other: Any) -> bool:
        """Inequality comparison."""
        result = self.__eq__(other)
        if result is NotImplemented:
            return NotImplemented
        return not result

    # Explicitly disallow comparison operators
    def __lt__(self, other: Any) -> bool:
        raise TypeError(
            f"'<' not supported between instances of '{self.__class__.__name__}' and '{other.__class__.__name__}'"
        )

    def __gt__(self, other: Any) -> bool:
        raise TypeError(
            f"'>' not supported between instances of '{self.__class__.__name__}' and '{other.__class__.__name__}'"
        )

    def __le__(self, other: Any) -> bool:
        raise TypeError(
            f"'<=' not supported between instances of '{self.__class__.__name__}' and '{other.__class__.__name__}'"
        )

    def __ge__(self, other: Any) -> bool:
        raise TypeError(
            f"'>=' not supported between instances of '{self.__class__.__name__}' and '{other.__class__.__name__}'"
        )


@dataclass
class VersionInfo:
    """Aggregated version information for a language"""

    latest: Optional[str] = None
    stable: Optional[str] = None
    recent_releases: List[ReleaseInfo] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def has_error(self) -> bool:
        """Check if the version info contains an error."""
        return "error" in self.details


def clean_version(version: str) -> str:
    """
    Clean version string by removing common prefixes and formatting

    Args:
        version: Version string to clean

    Returns:
        Cleaned version string
    """
    # Trim blanks
    version = version.strip()

    # Handle common prefixes
    prefixes = ["version", "python", "ruby", "node", "rust", "go", "v"]
    cleaned = version.lower()
    for prefix in prefixes:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix) :]
            break

    # Handle underscore-separated versions (like Ruby's v3_0_0)
    # Normalize consecutive underscores to a single
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    cleaned = cleaned.replace("_", ".")

    # Remove leading dot
    return cleaned.lstrip(".").strip()


def parse_semver(version: str) -> Tuple[int, ...]:
    """
    Parse semantic version string into tuple of integers

    Args:
        version: Version string to parse

    Returns:
        Tuple of version components as integers

    Raises:
        ValueError: If version string cannot be parsed
    """
    # Remove any prefix and clean the string
    version = clean_version(version)

    # Extract version numbers using regex
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", version)
    if not match:
        raise ValueError(f"Invalid version format: {version}")

    return tuple(map(int, match.groups()))


def standardize_date(date_str: Optional[str]) -> Optional[str]:
    """
    Convert various date formats to YYYY-MM-DD

    Args:
        date_str: Date string to standardize

    Returns:
        Standardized date string or None if input is None/invalid
    """
    if not date_str:
        return None

    try:
        # Handle ISO format dates (with or without timezone)
        date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return date.strftime("%Y-%m-%d")
    except ValueError:
        # Try parsing common date formats
        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"]:
            try:
                date = datetime.strptime(date_str, fmt)
                return date.strftime("%Y-%m-%d")
            except ValueError:
                continue

    return None


def is_prerelease(version: str) -> bool:
    """
    Check if a version string indicates a prerelease

    Args:
        version: Version string to check

    Returns:
        True if version is a prerelease, False otherwise
    """
    version_lower = version.lower()
    prerelease_indicators = [
        "alpha",
        "beta",
        "rc",
        "dev",
        "preview",
        "pre",
        "nightly",
        "snapshot",
        "test",
        "experimental",
    ]
    return any(indicator in version_lower for indicator in prerelease_indicators)


def check_github_api(
    session: Any,
    github_owner: str,
    github_repo: str,
    count: int = 5,
    filter_func: Optional[Callable[[Dict[str, Any]], bool]] = None,
) -> None:
    """
    Utility function to directly check GitHub API for tags

    Args:
        session: Requests session to use
        github_owner: GitHub repository owner
        github_repo: GitHub repository name
        count: Number of tags to display
        filter_func: Optional function to filter tags
    """
    url = f"https://api.github.com/repos/{github_owner}/{github_repo}/tags"
    print("\n=== Checking GitHub API ===")
    print(f"Checking {github_owner}/{github_repo} tags...")

    try:
        params = {"per_page": 100}  # Get more tags at once
        response = session.get(url, params=params, timeout=10)
        response.raise_for_status()
        tags = response.json()

        print(f"Status Code: {response.status_code}")
        print(f"Number of tags: {len(tags)}")

        if tags:
            # Filter tags if filter function is provided
            if filter_func:
                filtered_tags = [tag for tag in tags if filter_func(tag)]
                print(f"Number of filtered tags: {len(filtered_tags)}")
            else:
                filtered_tags = tags

            print(f"\nRecent version tags (max {count}):")
            for tag in filtered_tags[:count]:
                print(f"- {tag.get('name')}")
    except Exception as e:
        print(f"Error: {str(e)}")


def get_utc_now() -> datetime:
    """
    Helper function to get the current UTC time in a compatible way

    Returns:
        datetime: Current UTC time (without timezone information)

    Notes:
        From Python 3.11, datetime.utcnow() is deprecated,
        and datetime.now(datetime.UTC) is recommended.
        This function provides a compatible method using
        timezone.utc that works across all Python versions.
    """
    # Use timezone.utc available in all Python versions
    now = datetime.now(timezone.utc)

    # Return a datetime without timezone info, similar to datetime.utcnow()
    return now.replace(tzinfo=None)


def setup_logging(verbosity: int = 0) -> logging.Logger:
    """
    Set up logging with appropriate verbosity level

    Args:
        verbosity: Verbosity level (0=WARNING, 1=INFO, 2+=DEBUG)

    Returns:
        Configured root logger
    """
    # Configure log levels based on verbosity
    log_levels = [logging.WARNING, logging.INFO, logging.DEBUG]
    log_level = log_levels[min(verbosity, len(log_levels) - 1)]

    # Set up handler for stdout
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(levelname)s: %(message)s")
    handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    return root_logger
