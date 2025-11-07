"""Processor module for Claude activity generation.

This module contains the refactored processing pipeline components that break
down the monolithic ClaudeProcessor into focused, testable services.

Modules:
    logger_facade: Unified logging interface (CLI + session)
    limiter: Page limit enforcement (total + per-topic)
    page_processor: Single page processing with dependency injection
    pipeline: Clean orchestration flow

Design Principles:
    - Single Responsibility: Each module has one clear purpose
    - Dependency Injection: All dependencies via constructor
    - Testability First: 95%+ coverage target
    - Observable: Comprehensive logging at each layer

Version: 1.0.0 (Phase 6 Refactoring)
"""

from .logger_facade import LoggerFacade
from .limiter import PageLimiter, LimiterConfig
from .page_processor import PageProcessor, ProcessorConfig, ProcessedPage

__all__ = [
    "LoggerFacade",
    "PageLimiter",
    "LimiterConfig",
    "PageProcessor",
    "ProcessorConfig",
    "ProcessedPage",
]

__version__ = "1.0.0"
