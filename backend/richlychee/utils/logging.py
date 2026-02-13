"""구조화 로깅 (Rich 기반)."""

from __future__ import annotations

import logging

from rich.console import Console
from rich.logging import RichHandler

_console = Console(stderr=True)


def setup_logging(*, verbose: bool = False) -> logging.Logger:
    """애플리케이션 로거를 설정하고 반환."""
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                console=_console,
                rich_tracebacks=True,
                show_path=verbose,
            )
        ],
        force=True,
    )

    logger = logging.getLogger("richlychee")
    logger.setLevel(level)
    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """모듈별 로거 반환."""
    if name:
        return logging.getLogger(f"richlychee.{name}")
    return logging.getLogger("richlychee")


def get_console() -> Console:
    """Rich 콘솔 객체 반환."""
    return _console
