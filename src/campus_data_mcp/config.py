from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit, urlunsplit

Provider = Literal["csmar", "cnrds"]


@dataclass(frozen=True)
class ProviderSpec:
    name: str
    home: str
    domain: str
    note: str
    export_hosts: tuple[str, ...] = ()


PROVIDERS: dict[str, ProviderSpec] = {
    "csmar": ProviderSpec(
        "CSMAR",
        "https://data.csmar.com/",
        "csmar.com",
        "The website may log in automatically on a subscribed institution's IP. "
        "A public catalogue does not establish download entitlement.",
    ),
    "cnrds": ProviderSpec(
        "CNRDS",
        "https://www.cnrds.com/",
        "cnrds.com",
        "School login can provide basic databases. Specialty databases may require "
        "personal registration, even on campus. Sample access is not full access.",
        ("cnrds-file.oss-cn-shanghai.aliyuncs.com",),
    ),
}


class CampusError(Exception):
    """An actionable error whose message is safe to return to an agent."""


def spec_for(provider: str) -> ProviderSpec:
    try:
        return PROVIDERS[provider]
    except KeyError:
        raise CampusError("Provider must be 'csmar' or 'cnrds'.") from None


def safe_url(url: str) -> str:
    """Do not return signed query strings, fragments, or URL credentials."""
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"}:
        return parts.scheme + ":" if parts.scheme else ""
    return urlunsplit((parts.scheme, parts.hostname or "", parts.path, "", ""))


def allowed_url(provider: str, url: str, extra_hosts: tuple[str, ...] = ()) -> bool:
    parts = urlsplit(url)
    try:
        port = parts.port
    except ValueError:
        return False
    if parts.scheme != "https" or parts.username or parts.password or port not in {None, 443}:
        return False
    host = (parts.hostname or "").lower()
    spec = spec_for(provider)
    domain = spec.domain
    return (
        host == domain
        or host.endswith("." + domain)
        or host in spec.export_hosts
        or host in extra_hosts
    )


def private_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.chmod(0o700)
    return path


@dataclass(frozen=True)
class Settings:
    home: Path = field(
        default_factory=lambda: (
            Path(os.environ.get("CAMPUS_DATA_HOME", "~/.local/share/campus-data-mcp"))
            .expanduser()
            .resolve()
        )
    )
    headless: bool = False
    extra_hosts: tuple[str, ...] = ()
    min_interval: float = 1.0
    timeout_ms: int = 15000
    max_file_bytes: int = 512 * 1024 * 1024

    @classmethod
    def from_env(cls) -> Settings:
        hosts = tuple(
            h.strip().lower()
            for h in os.getenv("CAMPUS_DATA_EXTRA_HOSTS", "").split(",")
            if h.strip()
        )
        if any(not re.fullmatch(r"[a-z0-9.-]+", h) for h in hosts):
            raise CampusError("Extra hosts must be exact hostnames, without schemes or wildcards.")
        return cls(headless=os.getenv("CAMPUS_DATA_HEADLESS", "0") == "1", extra_hosts=hosts)
