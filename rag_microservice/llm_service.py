import os
import time
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate

from rag_microservice.observability import obs_manager, instrument_operation

class LLMService:
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.1):
        """
        Initialize the LLM service.
        
        Args:
            model_name: The OpenAI model to use
            temperature: Controls randomness in the response (0.0 = deterministic, 1.0 = very random)
        """
        self.model_name = model_name
        self.temperature = temperature
        
        # Initialize the LLM with LangSmith tracing
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            # Enable LangSmith tracing
            callbacks=[obs_manager.langchain_tracer] if obs_manager.langchain_tracer else None
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

    @instrument_operation("generate_response")
    def generate_response(self, question: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """
        Generate a response based on the question and retrieved chunks.
        
        Args:
            question: The user's question
            retrieved_chunks: List of retrieved chunks with metadata
            
        Returns:
            Generated response string
        """
        start_time = time.time()
        
        # Create a Langfuse trace for LLM generation
        trace = obs_manager.create_langfuse_trace(
            name="llm-generation",
            metadata={
                "model": self.model_name,
                "question": question,
                "num_sources": len(retrieved_chunks)
            }
        )
        
        try:
            if not retrieved_chunks:
                return "I couldn't find any relevant information to answer your question."
            
            # Create span for prompt preparation
            prompt_span = obs_manager.create_langfuse_span(trace, "prepare-prompt")
            
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

            if prompt_span:
                prompt_span.end(metadata={"context_length": len(context), "question_length": len(question)})
            
            # Create span for LLM call
            llm_span = obs_manager.create_langfuse_span(trace, "openai-call")
            
            # Generate response using the LLM
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=user_message)
            ]
            
            response = self.llm.invoke(messages)
            duration = time.time() - start_time
            
            if llm_span:
                llm_span.end(metadata={
                    "model": self.model_name,
                    "input_tokens": len(user_message.split()),
                    "output_tokens": len(response.content.split())
                })
            
            # Log the operation
            obs_manager.log_llm_operation(
                model=self.model_name,
                duration=duration,
                input_tokens=len(user_message.split()),
                output_tokens=len(response.content.split()),
                num_chunks=len(retrieved_chunks)
            )
            
            return response.content
            
        except Exception as e:
            duration = time.time() - start_time
            obs_manager.log_error("generate_response", e, model=self.model_name, num_chunks=len(retrieved_chunks))
            
            # Log error in trace if available
            if trace:
                error_span = trace.span(name="error", level="ERROR")
                error_span.end(metadata={"error": str(e), "error_type": type(e).__name__})
            
            return f"Error generating response: {str(e)}"
        finally:
            # Flush traces to ensure they are sent to Langfuse
            if trace:
                obs_manager.flush_langfuse()

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