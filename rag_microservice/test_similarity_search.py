import asyncio
from embeddings import embed_texts
from db import similarity_search

async def main():
    document_name = "short_pdf_CV.pdf"  # Change as needed
    query = input("Enter your query: ")
    print("Embedding query...")
    query_embedding = embed_texts([query])[0]
    print("Searching for similar chunks...")
    results = await similarity_search(query_embedding, document_name=document_name, top_k=3)
    print(f"Top {len(results)} results:")
    for i, res in enumerate(results, 1):
        print(f"\nResult {i} (page {res['page']}, distance {res['distance']:.4f}):\n{res['text'][:300]}\n{'-'*40}")

if __name__ == "__main__":
    asyncio.run(main()) 