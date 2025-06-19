import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import re
from pathlib import Path


def extract_sections_from_html(url: str, max_chunk_length: int = 2000) -> List[Dict[str, str]]:
    """
    Extract sections from HTML and chunk them if they exceed max_chunk_length.
    Returns a list of dicts: {"section": str, "text": str, "chunk_id": int}
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        chunks = []
        chunk_id = 1
        
        # Find all section headers (h1, h2, h3, etc.)
        headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        for i, header in enumerate(headers):
            section_name = header.get_text().strip()
            if not section_name:
                continue
                
            # Get content until the next header
            content = ""
            current = header.next_sibling
            
            while current and current.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                if hasattr(current, 'get_text'):
                    content += current.get_text() + " "
                current = current.next_sibling
            
            content = re.sub(r'\s+', ' ', content).strip()
            
            if not content:
                continue
            
            # Split content into chunks if it's too long
            if len(content) <= max_chunk_length:
                chunks.append({
                    "section": section_name,
                    "text": content,
                    "chunk_id": chunk_id
                })
                chunk_id += 1
            else:
                # Split into smaller chunks
                words = content.split()
                current_chunk = ""
                
                for word in words:
                    if len(current_chunk + " " + word) <= max_chunk_length:
                        current_chunk += " " + word if current_chunk else word
                    else:
                        if current_chunk:
                            chunks.append({
                                "section": section_name,
                                "text": current_chunk.strip(),
                                "chunk_id": chunk_id
                            })
                            chunk_id += 1
                        current_chunk = word
                
                # Add the last chunk
                if current_chunk:
                    chunks.append({
                        "section": section_name,
                        "text": current_chunk.strip(),
                        "chunk_id": chunk_id
                    })
                    chunk_id += 1
        
        return chunks
        
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return []


def save_chunks_to_file(chunks: List[Dict[str, str]], filename: str):
    """Save chunks to a text file for inspection."""
    with open(filename, 'w', encoding='utf-8') as f:
        for chunk in chunks:
            f.write(f"Section: {chunk['section']}\n")
            f.write(f"Chunk ID: {chunk['chunk_id']}\n")
            f.write(f"Text: {chunk['text']}\n")
            f.write("-" * 80 + "\n\n") 