from typing import List
from sentence_transformers import SentenceTransformer
import threading
import time
from rag_microservice.observability import obs_manager, instrument_operation

# Thread-safe singleton model loader
_model = None
_model_lock = threading.Lock()


def get_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    global _model
    with _model_lock:
        if _model is None:
            _model = SentenceTransformer(model_name)
        return _model


@instrument_operation("embed_texts")
def embed_texts(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for a list of texts."""
    start_time = time.time()
    
    try:
        model = get_model()
        embeddings = model.encode(texts, convert_to_tensor=False)
        duration = time.time() - start_time
        
        # Log the operation
        obs_manager.log_embedding_operation(
            operation="embed_texts",
            duration=duration,
            num_texts=len(texts),
            model_name="all-MiniLM-L6-v2"
        )
        
        return embeddings.tolist()
        
    except Exception as e:
        duration = time.time() - start_time
        obs_manager.log_error("embed_texts", e, num_texts=len(texts))
        raise 