#!/usr/bin/env python3
"""
Script to check if observability environment variables are properly loaded.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

def check_observability_env():
    """Check observability environment variables."""
    
    # Load .env file
    env_path = Path('.env')
    load_dotenv(env_path)
    
    print("Observability Environment Variables Check")
    print("=" * 50)
    
    # Check Langfuse variables
    langfuse_secret = os.getenv("LANGFUSE_SECRET_KEY")
    langfuse_public = os.getenv("LANGFUSE_PUBLIC_KEY")
    langfuse_host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    
    print("\nLangfuse Configuration:")
    print(f"  Secret Key: {'✅ Set' if langfuse_secret else '❌ Not set'}")
    print(f"  Public Key: {'✅ Set' if langfuse_public else '❌ Not set'}")
    print(f"  Host: {langfuse_host}")
    
    if langfuse_secret and langfuse_public:
        print("  ✅ Langfuse should be working")
    else:
        print("  ❌ Langfuse will not work - missing API keys")
    
    # Check LangSmith variables
    langsmith_key = os.getenv("LANGSMITH_API_KEY")
    
    print("\nLangSmith Configuration:")
    print(f"  API Key: {'✅ Set' if langsmith_key else '❌ Not set'}")
    
    if langsmith_key:
        print("  ✅ LangSmith should be working")
    else:
        print("  ❌ LangSmith will not work - missing API key")
    
    # Check if we can import and initialize observability
    try:
        from rag_microservice.observability import obs_manager
        print("\nObservability Manager:")
        print(f"  Langfuse initialized: {'✅ Yes' if obs_manager.langfuse else '❌ No'}")
        print(f"  LangSmith initialized: {'✅ Yes' if obs_manager.langsmith_client else '❌ No'}")
        
        if obs_manager.langfuse:
            print("  ✅ Langfuse client is ready")
        if obs_manager.langsmith_client:
            print("  ✅ LangSmith client is ready")
            
    except Exception as e:
        print(f"\n❌ Error initializing observability: {e}")

if __name__ == "__main__":
    check_observability_env() 