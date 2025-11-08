"""Processor module for Claude activity generation.

This module contains the refactored processing pipeline components that break
down the monolithic ClaudeProcessor into focused, testable services.

Modules:
    logger_facade: Unified logging interface (CLI + session)
    limiter: Page limit enforcement (total + per-topic)
    page_processor: Single page processing with dependency injection
    pipeline: Clean orchestration flow
    async_page_processor: Async page processing for concurrency
    async_pipeline: Async pipeline orchestration with semaphore control
    metrics: Processing metrics collection and export
    structured_logger: Structured logging with correlation IDs
    backends: AI backend plugin system (Claude, future: OpenAI, etc.)

Design Principles:
    - Single Responsibility: Each module has one clear purpose
    - Dependency Injection: All dependencies via constructor
    - Testability First: 95%+ coverage target
    - Observable: Comprehensive logging at each layer
    - Plugin Architecture: Swappable AI backends

Version: 1.1.0 (Phase 7 Enhancements)
"""

from .logger_facade import LoggerFacade
from .limiter import PageLimiter, LimiterConfig
from .page_processor import PageProcessor, ProcessorConfig, ProcessedPage
from .pipeline import ProcessingPipeline, PipelineConfig, PipelineResult
from .async_page_processor import AsyncPageProcessor
from .async_pipeline import AsyncProcessingPipeline, AsyncPipelineConfig, AsyncPipelineResult
from .metrics import ProcessingMetrics, MetricsCollector
from .structured_logger import StructuredLogger, LogEntry
from .backends import AIBackend, ClaudeBackend, BackendFactory

__all__ = [
    "LoggerFacade",
    "PageLimiter",
    "LimiterConfig",
    "PageProcessor",
    "ProcessorConfig",
    "ProcessedPage",
    "ProcessingPipeline",
    "PipelineConfig",
    "PipelineResult",
    "AsyncPageProcessor",
    "AsyncProcessingPipeline",
    "AsyncPipelineConfig",
    "AsyncPipelineResult",
    "ProcessingMetrics",
    "MetricsCollector",
    "StructuredLogger",
    "LogEntry",
    "AIBackend",
    "ClaudeBackend",
    "BackendFactory",
]

__version__ = "1.1.0"
