from typing import List
from sentence_transformers import SentenceTransformer
import threading

# Thread-safe singleton model loader
_model = None
_model_lock = threading.Lock()


def get_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    global _model
    with _model_lock:
        if _model is None:
            _model = SentenceTransformer(model_name)
        return _model


def embed_texts(texts: List[str], model_name: str = "all-MiniLM-L6-v2") -> List[List[float]]:
    """
    Embed a list of texts into vectors using Sentence Transformers.
    Returns a list of embedding vectors (lists of floats).
    """
    model = get_model(model_name)
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return embeddings.tolist() 