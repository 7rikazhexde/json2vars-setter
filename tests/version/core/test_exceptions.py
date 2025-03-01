import pytest

from json2vars_setter.version.core.exceptions import (
    GitHubAPIError,
    ParseError,
    ValidationError,
    VersionFetchError,
)


def test_version_fetch_error_is_exception() -> None:
    """Test that VersionFetchError is a subclass of Exception"""
    assert issubclass(VersionFetchError, Exception)


def test_github_api_error_inheritance() -> None:
    """Test that GitHubAPIError is a subclass of VersionFetchError"""
    assert issubclass(GitHubAPIError, VersionFetchError)


def test_parse_error_inheritance() -> None:
    """Test that ParseError is a subclass of VersionFetchError"""
    assert issubclass(ParseError, VersionFetchError)


def test_validation_error_inheritance() -> None:
    """Test that ValidationError is a subclass of VersionFetchError"""
    assert issubclass(ValidationError, VersionFetchError)


def test_version_fetch_error_instantiation() -> None:
    """Test that VersionFetchError can be instantiated with a message"""
    error_msg = "Test error message"
    error = VersionFetchError(error_msg)
    assert str(error) == error_msg


def test_github_api_error_instantiation() -> None:
    """Test that GitHubAPIError can be instantiated with a message"""
    error_msg = "GitHub API error"
    error = GitHubAPIError(error_msg)
    assert str(error) == error_msg
    assert isinstance(error, VersionFetchError)


def test_parse_error_instantiation() -> None:
    """Test that ParseError can be instantiated with a message"""
    error_msg = "Failed to parse version"
    error = ParseError(error_msg)
    assert str(error) == error_msg
    assert isinstance(error, VersionFetchError)


def test_validation_error_instantiation() -> None:
    """Test that ValidationError can be instantiated with a message"""
    error_msg = "Invalid version format"
    error = ValidationError(error_msg)
    assert str(error) == error_msg
    assert isinstance(error, VersionFetchError)


def test_error_hierarchy() -> None:
    """Test the full error hierarchy"""
    # Create a chain of try/except blocks to verify the hierarchy
    try:
        # Raise a specific error
        raise ParseError("Could not parse version")
    except ValidationError:
        pytest.fail("ParseError should not be caught by ValidationError")
    except ParseError:
        # This should catch
        try:
            # Re-raise the caught error
            raise
        except VersionFetchError:
            # This should catch the re-raised error
            pass
        else:
            pytest.fail("ParseError should be caught by VersionFetchError")
    except Exception:
        pytest.fail("ParseError should be caught before generic Exception")
    else:
        pytest.fail("ParseError was not caught")
