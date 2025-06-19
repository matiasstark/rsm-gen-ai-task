#!/usr/bin/env python3
"""
Test script to verify LangSmith integration is working.
"""

import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path('.env')
load_dotenv(env_path)

async def test_langsmith_integration():
    """Test LangSmith integration by creating a trace."""
    
    print("Testing LangSmith Integration")
    print("=" * 40)
    
    # Check environment variables
    langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
    
    if not langsmith_api_key:
        print("❌ LangSmith API key not found in environment variables")
        print("Please check your .env file contains:")
        print("LANGSMITH_API_KEY=your_api_key")
        return
    
    print(f"✅ LangSmith API key found")
    print(f"  API Key: {langsmith_api_key[:10]}...")
    
    try:
        # Set required environment variables
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
        os.environ["LANGCHAIN_API_KEY"] = langsmith_api_key
        os.environ["LANGCHAIN_PROJECT"] = "rag-microservice-test"
        
        # Import and test LangChain with LangSmith
        from langchain_openai import ChatOpenAI
        from langchain.schema import HumanMessage, SystemMessage
        from langchain.callbacks import LangChainTracer
        
        print("✅ LangChain environment variables set")
        
        # Create tracer
        tracer = LangChainTracer()
        print("✅ LangChain tracer created")
        
        # Create LLM with tracing
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            callbacks=[tracer]
        )
        
        print("✅ LLM with tracing created")
        
        # Create a test message
        messages = [
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content="Say hello and tell me the current time.")
        ]
        
        print("✅ Test messages created")
        
        # Make the call (this should create a trace in LangSmith)
        response = llm.invoke(messages)
        
        print("✅ LLM call completed")
        print(f"Response: {response.content}")
        print("\n🎉 LangSmith integration test completed!")
        print("Check your LangSmith dashboard for the test trace.")
        print("Project: rag-microservice-test")
        
    except Exception as e:
        print(f"❌ Error testing LangSmith integration: {e}")
        print("This could be due to:")
        print("1. Invalid API keys")
        print("2. Network connectivity issues")
        print("3. LangSmith service being down")

if __name__ == "__main__":
    asyncio.run(test_langsmith_integration()) 