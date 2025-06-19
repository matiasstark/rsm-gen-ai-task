-- Create the rag_chunks table
CREATE TABLE IF NOT EXISTS rag_chunks (
    id SERIAL PRIMARY KEY,
    document_name TEXT NOT NULL,
    page INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding VECTOR(384),
    source_type TEXT,
    section_name TEXT,
    url TEXT,
    is_overlap BOOLEAN DEFAULT FALSE
); 