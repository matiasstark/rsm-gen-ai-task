import os
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate

class LLMService:
    def __init__(self, model_name: str = "gpt-3.5-turbo", temperature: float = 0.1):
        """
        Initialize the LLM service.
        
        Args:
            model_name: The OpenAI model to use
            temperature: Controls randomness in the response (0.0 = deterministic, 1.0 = very random)
        """
        self.model_name = model_name
        self.temperature = temperature
        
        # Initialize the LLM
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Define the system prompt for RAG responses
        self.system_prompt = """You are a helpful AI assistant that answers questions based on the provided context. 

Your task is to:
1. Analyze the provided context carefully
2. Answer the user's question using only information from the context
3. If the context doesn't contain enough information to answer the question, say so clearly
4. Provide accurate, helpful, and well-structured responses
5. Cite specific sections or sources when possible

Always be honest about what you know and don't know based on the provided context."""

    def generate_response(self, question: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """
        Generate a response based on the question and retrieved chunks.
        
        Args:
            question: The user's question
            retrieved_chunks: List of retrieved chunks with metadata
            
        Returns:
            Generated response string
        """
        if not retrieved_chunks:
            return "I couldn't find any relevant information to answer your question."
        
        # Format the context from retrieved chunks
        context_parts = []
        for i, chunk in enumerate(retrieved_chunks, 1):
            source_info = f"[Source {i}]"
            if chunk.get("source_type"):
                source_info += f" {chunk['source_type']}"
            if chunk.get("section_name"):
                source_info += f" - {chunk['section_name']}"
            if chunk.get("url"):
                source_info += f" ({chunk['url']})"
            
            context_parts.append(f"{source_info}\n{chunk['text']}\n")
        
        context = "\n".join(context_parts)
        
        # Create the user message with context and question
        user_message = f"""Context:
{context}

Question: {question}

Please provide a comprehensive answer based on the context above. If the context doesn't contain enough information to fully answer the question, please say so and provide what information is available."""

        try:
            # Generate response using the LLM
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=user_message)
            ]
            
            response = self.llm.invoke(messages)
            return response.content
            
        except Exception as e:
            return f"Error generating response: {str(e)}"

    def generate_response_with_sources(self, question: str, retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a response with source information.
        
        Args:
            question: The user's question
            retrieved_chunks: List of retrieved chunks with metadata
            
        Returns:
            Dictionary containing response and source information
        """
        response = self.generate_response(question, retrieved_chunks)
        
        # Extract source information
        sources = []
        for chunk in retrieved_chunks:
            source_info = {
                "text": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"],
                "source_type": chunk.get("source_type"),
                "section_name": chunk.get("section_name"),
                "url": chunk.get("url"),
                "distance": chunk.get("distance")
            }
            sources.append(source_info)
        
        return {
            "answer": response,
            "sources": sources,
            "num_sources": len(sources)
        } 