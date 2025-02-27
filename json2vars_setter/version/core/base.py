import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests

from json2vars_setter.version.core.exceptions import GitHubAPIError, ParseError
from json2vars_setter.version.core.utils import ReleaseInfo, VersionInfo


class BaseVersionFetcher(ABC):
    """Base class for version fetchers that use GitHub tags"""

    def __init__(self, github_owner: str, github_repo: str):
        """
        Initialize the fetcher with GitHub repository information

        Args:
            github_owner: GitHub repository owner
            github_repo: GitHub repository name
        """
        self.github_owner = github_owner
        self.github_repo = github_repo
        self.github_api_base = "https://api.github.com"
        self.logger = logging.getLogger(self.__class__.__name__)

        # Initialize session with common headers
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "json2vars-setter",
            }
        )

        # GitHub token configuration (from environment variable)
        self.github_token = os.environ.get("GITHUB_TOKEN")
        if self.github_token:
            self.session.headers.update(
                {"Authorization": "token {}".format(self.github_token)}
            )

    def _get_github_tags(self, count: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch tags from GitHub API with pagination to ensure enough stable versions

        Args:
            count: Optional number of tags to return

        Returns:
            List of tag information

        Raises:
            GitHubAPIError: If there's an error accessing the GitHub API
        """
        stable_tags: List[Dict[str, Any]] = []
        page = 1
        per_page = 100  # Get more tags at once
        max_pages = 5  # Safety limit for pagination
        target_count = count or 5

        self.logger.debug("Fetching stable tags (target count: %d)", target_count)

        # Continue until we have enough stable tags
        while len(stable_tags) < target_count and page <= max_pages:
            url = "{}/repos/{}/{}/tags".format(
                self.github_api_base, self.github_owner, self.github_repo
            )
            params = {"page": page, "per_page": per_page}

            self.logger.debug("Fetching page %d (per_page=%d)", page, per_page)

            try:
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                tags = response.json()

                self.logger.debug("Got %d tags from API", len(tags))

                if not tags:  # No more tags
                    self.logger.debug("No more tags found, breaking")
                    break

                # Filter for stable tags using the language-specific filter
                new_stable_tags = [tag for tag in tags if self._is_stable_tag(tag)]

                self.logger.debug(
                    "Found %d stable tags in this page", len(new_stable_tags)
                )
                if new_stable_tags:
                    tag_samples = [tag.get("name") for tag in new_stable_tags[:3]]
                    self.logger.debug("First few stable tags: %s", tag_samples)

                stable_tags.extend(new_stable_tags)
                self.logger.debug("Total stable tags so far: %d", len(stable_tags))

                if len(tags) < per_page:  # Last page
                    self.logger.debug("Last page reached, breaking")
                    break

                page += 1

            except requests.exceptions.RequestException as error:
                response_status = getattr(error.response, "status_code", None)
                if response_status == 403 and "rate limit exceeded" in str(error):
                    message = (
                        "GitHub API rate limit exceeded. "
                        "Please set GITHUB_TOKEN environment variable "
                        "or wait for rate limit reset."
                    )
                    raise GitHubAPIError(message)
                raise GitHubAPIError(
                    "Failed to fetch GitHub tags: {}".format(str(error))
                )

        result = stable_tags[:target_count] if target_count else stable_tags
        self.logger.debug("Returning %d stable tags", len(result))
        return result

    @abstractmethod
    def _is_stable_tag(self, tag: Dict[str, Any]) -> bool:
        """
        Check if a tag represents a stable release

        Args:
            tag: Tag information from GitHub API

        Returns:
            True if the tag represents a stable release, False otherwise
        """
        pass

    @abstractmethod
    def _parse_version_from_tag(self, tag: Dict[str, Any]) -> ReleaseInfo:
        """
        Parse version information from a tag object

        Args:
            tag: Tag data from GitHub API

        Returns:
            Parsed ReleaseInfo object
        """
        pass

    def _get_additional_info(self) -> Dict[str, Any]:
        """
        Get additional information specific to the language

        Returns:
            Dictionary with additional language-specific information
        """
        # By default, no additional information
        return {}

    def _get_stability_criteria(
        self, releases: List[ReleaseInfo]
    ) -> Tuple[ReleaseInfo, ReleaseInfo]:
        """
        Determine latest and stable versions from releases

        Args:
            releases: List of release information

        Returns:
            Tuple of (latest_release, stable_release)
        """
        # Ensure the function always returns non-None ReleaseInfo objects
        if not releases:
            raise ValueError("No releases available")

        # By default, latest is first release and stable is the same
        return releases[0], releases[0]

    def fetch_versions(self, recent_count: int = 5) -> VersionInfo:
        """
        Fetch version information

        Args:
            recent_count: Number of recent stable releases to include

        Returns:
            VersionInfo object containing version information
        """
        try:
            # Get tags from GitHub
            tags = self._get_github_tags(recent_count)
            if not tags:
                return VersionInfo(details={"error": "No releases found"})

            # Parse all tags
            release_infos = []
            for tag in tags:
                try:
                    release_info = self._parse_version_from_tag(tag)
                    release_infos.append(release_info)
                except ParseError:
                    continue

            if not release_infos:
                return VersionInfo(details={"error": "Failed to parse any releases"})

            # Get additional language-specific information
            additional_info = self._get_additional_info()

            # Filter recent releases - make sure we don't exceed the requested count
            recent_releases = release_infos[:recent_count]
            self.logger.debug("Using %d recent releases", len(recent_releases))

            # Get latest and stable releases
            latest, stable = self._get_stability_criteria(release_infos)

            # Create result
            return VersionInfo(
                latest=latest.version if latest else None,
                stable=stable.version if stable else None,
                recent_releases=recent_releases,
                details={
                    "fetch_time": datetime.utcnow().isoformat(),
                    "source": "github:{}/{}".format(
                        self.github_owner, self.github_repo
                    ),
                    "latest_info": vars(latest) if latest else None,
                    "stable_info": vars(stable) if stable else None,
                    **additional_info,
                },
            )
        except Exception as error:
            self.logger.error("Error fetching versions: %s", str(error), exc_info=True)
            return VersionInfo(
                details={"error": str(error), "error_type": type(error).__name__}
            )
