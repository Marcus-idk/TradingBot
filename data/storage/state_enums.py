"""Type-safe enums for provider watermark scopes and streams."""

from __future__ import annotations

from enum import Enum


class Provider(Enum):
    """Supported news/data providers tracked by watermark state."""

    FINNHUB = "FINNHUB"
    POLYGON = "POLYGON"


class Stream(Enum):
    """Logical stream identifiers within a provider."""

    COMPANY = "COMPANY"
    MACRO = "MACRO"


class Scope(Enum):
    """Watermark scope (global vs per-symbol)."""

    GLOBAL = "GLOBAL"
    SYMBOL = "SYMBOL"
