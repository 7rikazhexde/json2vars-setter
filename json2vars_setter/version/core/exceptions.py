class VersionFetchError(Exception):
    """Base exception for version fetching errors"""

    pass


class GitHubAPIError(VersionFetchError):
    """Raised when there's an error accessing the GitHub API"""

    pass


class ParseError(VersionFetchError):
    """Raised when there's an error parsing version information"""

    pass


class ValidationError(VersionFetchError):
    """Raised when version data validation fails"""

    pass
