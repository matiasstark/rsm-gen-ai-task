import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from rag_microservice.llm_service import LLMService
from rag_microservice.embeddings import embed_texts
from rag_microservice.db import similarity_search

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

async def test_llm_integration():
    """Test the LLM integration with a sample query."""
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not set. Please set it to test LLM integration.")
        print(f"Looking for .env file at: {env_path}")
        if env_path.exists():
            print(".env file exists but OPENAI_API_KEY not found in it.")
        else:
            print(".env file not found.")
        return
    
    print("Testing LLM integration...")
    
    # Initialize LLM service
    llm_service = LLMService()
    
    # Sample query
    question = "What is PEP 8?"
    
    print(f"Query: {question}")
    
    try:
        # Perform semantic search
        query_embedding = embed_texts([question])[0]
        results = await similarity_search(query_embedding, top_k=3)
        
        if not results:
            print("No chunks found for the query.")
            return
        
        print(f"Found {len(results)} relevant chunks")
        
        # Generate response using LLM
        llm_response = llm_service.generate_response_with_sources(question, results)
        
        print("\n" + "="*50)
        print("LLM Response:")
        print("="*50)
        print(llm_response["answer"])
        
        print(f"\nSources used: {llm_response['num_sources']}")
        for i, source in enumerate(llm_response["sources"], 1):
            print(f"\nSource {i}:")
            print(f"  Type: {source['source_type']}")
            print(f"  Section: {source['section_name']}")
            print(f"  Distance: {source['distance']:.4f}")
            print(f"  Preview: {source['text'][:100]}...")
        
        print("\nLLM integration test completed successfully!")
        
    except Exception as e:
        print(f"Error during LLM integration test: {e}")

if __name__ == "__main__":
    asyncio.run(test_llm_integration()) 