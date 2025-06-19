import asyncio
import time
from rag_microservice.observability import obs_manager, logger

async def test_observability():
    """Test the observability setup."""
    
    print("Testing Observability Setup")
    print("=" * 40)
    
    # Test structured logging
    logger.info("Test log message", test_field="test_value")
    logger.warning("Test warning message", warning_level="medium")
    logger.error("Test error message", error_code="TEST_001")
    
    # Test request logging
    obs_manager.log_request(
        endpoint="/test",
        method="GET",
        status_code=200,
        duration=0.123,
        test_param="test_value"
    )
    
    # Test error logging
    try:
        raise ValueError("Test error for observability")
    except Exception as e:
        obs_manager.log_error("/test", e, test_context="observability_test")
    
    # Test embedding operation logging
    obs_manager.log_embedding_operation(
        operation="test_embed",
        duration=0.456,
        num_texts=5,
        model_name="test-model"
    )
    
    # Test search operation logging
    obs_manager.log_search_operation(
        operation="test_search",
        duration=0.789,
        num_results=3,
        top_k=5
    )
    
    # Test LLM operation logging
    obs_manager.log_llm_operation(
        model="gpt-4o-mini",
        duration=1.234,
        input_tokens=100,
        output_tokens=50
    )
    
    # Test ingestion operation logging
    obs_manager.log_ingestion_operation(
        source_type="test_source",
        duration=2.345,
        num_chunks=10
    )
    
    # Test trace operation context manager
    async with obs_manager.trace_operation("test_trace", test_param="trace_value"):
        await asyncio.sleep(0.1)  # Simulate some work
        print("Trace operation completed")
    
    print("\n✅ All observability tests completed!")
    print("Check your logs and metrics to verify the data is being captured.")

if __name__ == "__main__":
    asyncio.run(test_observability()) 