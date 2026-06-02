"""Tests for json2vars_setter.version.registry"""

import pytest

from json2vars_setter.version.fetchers.go import GoVersionFetcher
from json2vars_setter.version.fetchers.nodejs import NodejsVersionFetcher
from json2vars_setter.version.fetchers.python import PythonVersionFetcher
from json2vars_setter.version.fetchers.ruby import RubyVersionFetcher
from json2vars_setter.version.fetchers.rust import RustVersionFetcher
from json2vars_setter.version.registry import get_version_fetcher


def test_get_version_fetcher_returns_expected_type() -> None:
    """get_version_fetcher returns the correct fetcher instance for each language"""
    assert isinstance(get_version_fetcher("python"), PythonVersionFetcher)
    assert isinstance(get_version_fetcher("nodejs"), NodejsVersionFetcher)
    assert isinstance(get_version_fetcher("ruby"), RubyVersionFetcher)
    assert isinstance(get_version_fetcher("go"), GoVersionFetcher)
    assert isinstance(get_version_fetcher("rust"), RustVersionFetcher)


def test_get_version_fetcher_unsupported_language() -> None:
    """get_version_fetcher raises ValueError for an unknown language"""
    with pytest.raises(ValueError, match="Unsupported language: invalid"):
        get_version_fetcher("invalid")
