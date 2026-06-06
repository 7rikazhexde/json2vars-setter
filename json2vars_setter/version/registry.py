"""
Central registry mapping language names to their version fetchers.

This is the single source of truth for which fetcher handles each language,
shared by the matrix-update and version-cache features.
"""

from typing import Callable, Dict

from json2vars_setter.version.core.base import BaseVersionFetcher
from json2vars_setter.version.fetchers.bun import BunVersionFetcher
from json2vars_setter.version.fetchers.crystal import CrystalVersionFetcher
from json2vars_setter.version.fetchers.dart import DartVersionFetcher
from json2vars_setter.version.fetchers.deno import DenoVersionFetcher
from json2vars_setter.version.fetchers.dotnet import DotnetVersionFetcher
from json2vars_setter.version.fetchers.elixir import ElixirVersionFetcher
from json2vars_setter.version.fetchers.go import GoVersionFetcher
from json2vars_setter.version.fetchers.java import JavaVersionFetcher
from json2vars_setter.version.fetchers.julia import JuliaVersionFetcher
from json2vars_setter.version.fetchers.nodejs import NodejsVersionFetcher
from json2vars_setter.version.fetchers.php import PhpVersionFetcher
from json2vars_setter.version.fetchers.python import PythonVersionFetcher
from json2vars_setter.version.fetchers.ruby import RubyVersionFetcher
from json2vars_setter.version.fetchers.rust import RustVersionFetcher
from json2vars_setter.version.fetchers.swift import SwiftVersionFetcher
from json2vars_setter.version.fetchers.zig import ZigVersionFetcher

# Supported languages mapped to their fetcher factories (each concrete fetcher
# takes no constructor arguments).
LANGUAGE_FETCHERS: Dict[str, Callable[[], BaseVersionFetcher]] = {
    "python": PythonVersionFetcher,
    "nodejs": NodejsVersionFetcher,
    "ruby": RubyVersionFetcher,
    "go": GoVersionFetcher,
    "rust": RustVersionFetcher,
    "php": PhpVersionFetcher,
    "dotnet": DotnetVersionFetcher,
    "java": JavaVersionFetcher,
    "deno": DenoVersionFetcher,
    "bun": BunVersionFetcher,
    "zig": ZigVersionFetcher,
    "elixir": ElixirVersionFetcher,
    "dart": DartVersionFetcher,
    "swift": SwiftVersionFetcher,
    "julia": JuliaVersionFetcher,
    "crystal": CrystalVersionFetcher,
}


def get_version_fetcher(language: str) -> BaseVersionFetcher:
    """
    Get the appropriate version fetcher for the language

    Args:
        language: Programming language name

    Returns:
        Instantiated version fetcher for the specified language

    Raises:
        ValueError: If language is not supported
    """
    if language not in LANGUAGE_FETCHERS:
        raise ValueError(f"Unsupported language: {language}")

    return LANGUAGE_FETCHERS[language]()
