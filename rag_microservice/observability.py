import os
import time
import asyncio
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager
from functools import wraps

import structlog
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from langfuse import Langfuse
from langsmith import Client as LangSmithClient
from langchain.callbacks import LangChainTracer
from langchain.callbacks.tracers import LangChainTracer

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Prometheus Metrics
REQUEST_COUNT = Counter('rag_requests_total', 'Total number of RAG requests', ['endpoint', 'status'])
REQUEST_DURATION = Histogram('rag_request_duration_seconds', 'Request duration in seconds', ['endpoint'])
EMBEDDING_DURATION = Histogram('embedding_duration_seconds', 'Embedding computation duration', ['operation'])
SEARCH_DURATION = Histogram('search_duration_seconds', 'Similarity search duration', ['operation'])
LLM_DURATION = Histogram('llm_duration_seconds', 'LLM inference duration', ['model'])
ERROR_COUNT = Counter('rag_errors_total', 'Total number of errors', ['endpoint', 'error_type'])
ACTIVE_CHUNKS = Gauge('active_chunks_total', 'Total number of chunks in database')
INGESTION_DURATION = Histogram('ingestion_duration_seconds', 'Data ingestion duration', ['source_type'])

class ObservabilityManager:
    """Manages observability for the RAG system."""
    
    def __init__(self):
        self.langfuse = None
        self.langsmith_client = None
        self.langchain_tracer = None
        
        # Initialize Langfuse if API key is available
        langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        langfuse_host = os.getenv("LANGFUSE_HOST", "https://us.cloud.langfuse.com")
        
        if langfuse_secret_key and langfuse_public_key:
            self.langfuse = Langfuse(
                secret_key=langfuse_secret_key,
                public_key=langfuse_public_key,
                host=langfuse_host
            )
            logger.info("Langfuse initialized", host=langfuse_host)
        
        # Initialize LangSmith if API key is available
        langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
        if langsmith_api_key:
            self.langsmith_client = LangSmithClient(api_key=langsmith_api_key)
            self.langchain_tracer = LangChainTracer()
            logger.info("LangSmith initialized")
    
    def log_request(self, endpoint: str, method: str, status_code: int, duration: float, **kwargs):
        """Log incoming request details."""
        logger.info(
            "Request processed",
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            duration=duration,
            **kwargs
        )
        
        # Update Prometheus metrics
        REQUEST_COUNT.labels(endpoint=endpoint, status=status_code).inc()
        REQUEST_DURATION.labels(endpoint=endpoint).observe(duration)
    
    def log_error(self, endpoint: str, error: Exception, **kwargs):
        """Log error details."""
        logger.error(
            "Error occurred",
            endpoint=endpoint,
            error_type=type(error).__name__,
            error_message=str(error),
            **kwargs
        )
        
        ERROR_COUNT.labels(endpoint=endpoint, error_type=type(error).__name__).inc()
    
    def log_embedding_operation(self, operation: str, duration: float, num_texts: int, **kwargs):
        """Log embedding operation details."""
        logger.info(
            "Embedding operation completed",
            operation=operation,
            duration=duration,
            num_texts=num_texts,
            **kwargs
        )
        
        EMBEDDING_DURATION.labels(operation=operation).observe(duration)
    
    def log_search_operation(self, operation: str, duration: float, num_results: int, **kwargs):
        """Log search operation details."""
        logger.info(
            "Search operation completed",
            operation=operation,
            duration=duration,
            num_results=num_results,
            **kwargs
        )
        
        SEARCH_DURATION.labels(operation=operation).observe(duration)
    
    def log_llm_operation(self, model: str, duration: float, input_tokens: int = None, output_tokens: int = None, **kwargs):
        """Log LLM operation details."""
        logger.info(
            "LLM operation completed",
            model=model,
            duration=duration,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            **kwargs
        )
        
        LLM_DURATION.labels(model=model).observe(duration)
    
    def log_ingestion_operation(self, source_type: str, duration: float, num_chunks: int, **kwargs):
        """Log ingestion operation details."""
        logger.info(
            "Ingestion operation completed",
            source_type=source_type,
            duration=duration,
            num_chunks=num_chunks,
            **kwargs
        )
        
        INGESTION_DURATION.labels(source_type=source_type).observe(duration)
        ACTIVE_CHUNKS.inc(num_chunks)
    
    @asynccontextmanager
    async def trace_operation(self, operation_name: str, **kwargs):
        """Context manager for tracing operations."""
        start_time = time.time()
        try:
            yield
        except Exception as e:
            self.log_error(operation_name, e, **kwargs)
            raise
        finally:
            duration = time.time() - start_time
            logger.info(
                "Operation completed",
                operation=operation_name,
                duration=duration,
                **kwargs
            )
    
    def create_langfuse_trace(self, name: str, **kwargs):
        """Create a Langfuse trace."""
        if self.langfuse:
            return self.langfuse.trace(name=name, **kwargs)
        return None
    
    def create_langfuse_span(self, trace, name: str, **kwargs):
        """Create a Langfuse span."""
        if trace:
            return trace.span(name=name, **kwargs)
        return None
    
    def flush_langfuse(self):
        """Flush Langfuse traces to ensure they are sent immediately."""
        if self.langfuse:
            try:
                self.langfuse.flush()
                logger.debug("Langfuse traces flushed successfully")
            except Exception as e:
                logger.error("Failed to flush Langfuse traces", error=str(e))
    
    async def flush_langfuse_async(self):
        """Async version of flush_langfuse."""
        if self.langfuse:
            try:
                await self.langfuse.flush_async()
                logger.debug("Langfuse traces flushed successfully (async)")
            except Exception as e:
                logger.error("Failed to flush Langfuse traces (async)", error=str(e))

# Global observability manager instance
obs_manager = ObservabilityManager()

def instrument_operation(operation_name: str):
    """Decorator to instrument operations with observability."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(
                    "Operation completed successfully",
                    operation=operation_name,
                    duration=duration
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                obs_manager.log_error(operation_name, e)
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(
                    "Operation completed successfully",
                    operation=operation_name,
                    duration=duration
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                obs_manager.log_error(operation_name, e)
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def get_metrics():
    """Get Prometheus metrics."""
    return generate_latest()

def get_metrics_content_type():
    """Get Prometheus metrics content type."""
    return CONTENT_TYPE_LATEST 