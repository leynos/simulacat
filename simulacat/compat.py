"""Compatibility helpers for optional extensions."""

from __future__ import annotations

try:  # pragma: no cover - Rust optional
    rust = __import__("_simulacat_rs")
    hello = rust.hello
except ModuleNotFoundError:  # pragma: no cover - Python fallback
    from .pure import hello

__all__ = ["hello"]
