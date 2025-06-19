#!/usr/bin/env python3
"""
Test script to verify Langfuse integration is working.
"""

import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path('.env')
load_dotenv(env_path)

async def test_langfuse_integration():
    """Test Langfuse integration by creating a trace."""
    
    print("Testing Langfuse Integration")
    print("=" * 40)
    
    # Check environment variables
    langfuse_secret = os.getenv("LANGFUSE_SECRET_KEY")
    langfuse_public = os.getenv("LANGFUSE_PUBLIC_KEY")
    
    if not langfuse_secret or not langfuse_public:
        print("❌ Langfuse API keys not found in environment variables")
        print("Please check your .env file contains:")
        print("LANGFUSE_SECRET_KEY=your_secret_key")
        print("LANGFUSE_PUBLIC_KEY=your_public_key")
        return
    
    print(f"✅ Langfuse API keys found")
    print(f"  Secret Key: {langfuse_secret[:10]}...")
    print(f"  Public Key: {langfuse_public[:10]}...")
    
    try:
        # Import and test Langfuse
        from langfuse import Langfuse
        
        langfuse = Langfuse(
            secret_key=langfuse_secret,
            public_key=langfuse_public
        )
        
        print("✅ Langfuse client created successfully")
        
        # Create a test trace
        trace = langfuse.trace(
            name="test-rag-integration",
            metadata={"test": True, "source": "rag-microservice"}
        )
        
        print("✅ Test trace created")
        
        # Create a test span
        span = trace.span(
            name="test-operation",
            metadata={"operation": "test", "duration": 0.1}
        )
        
        print("✅ Test span created")
        
        # End the span and trace
        span.end()
        #trace.close()
        
        print("✅ Test trace and span ended")
        print("\n🎉 Langfuse integration test completed!")
        print("Check your Langfuse dashboard for the test trace.")
        
    except Exception as e:
        print(f"❌ Error testing Langfuse integration: {e}")
        print("This could be due to:")
        print("1. Invalid API keys")
        print("2. Network connectivity issues")
        print("3. Langfuse service being down")

if __name__ == "__main__":
    asyncio.run(test_langfuse_integration()) 