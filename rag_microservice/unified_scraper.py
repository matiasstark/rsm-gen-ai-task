import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re
from urllib.parse import urljoin, urlparse
import time


class UnifiedWebScraper:
    def __init__(self, max_chunk_length: int = 1500, overlap_length: int = 100):
        self.max_chunk_length = max_chunk_length
        self.overlap_length = overlap_length
    
    def scrape_think_python(self, base_url: str = "https://allendowney.github.io/ThinkPython/") -> List[Dict[str, str]]:
        """Scrape all chapters of Think Python book."""
        all_chunks = []
        
        # Chapters from 0 to 19 (chap00.html to chap19.html)
        for chapter_num in range(20):
            chapter_url = f"{base_url}chap{chapter_num:02d}.html"
            print(f"Scraping chapter {chapter_num}: {chapter_url}")
            
            try:
                chunks = self._scrape_single_page(
                    chapter_url, 
                    source_type="think_python",
                    chapter_num=chapter_num
                )
                all_chunks.extend(chunks)
                time.sleep(1)  # Be respectful to the server
                
            except Exception as e:
                print(f"Error scraping chapter {chapter_num}: {e}")
                continue
        
        return all_chunks
    
    def scrape_pep8(self, url: str = "https://peps.python.org/pep-0008/") -> List[Dict[str, str]]:
        """Scrape PEP 8 style guide by h2 sections."""
        return self._scrape_pep8_by_sections(url)
    
    def _scrape_pep8_by_sections(self, url: str) -> List[Dict[str, str]]:
        """Scrape PEP 8 by chunking each h2 section separately, including content in <section> siblings."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get the main content area - focus on the actual content
            main_content = self._get_main_content(soup, "pep8")
            
            if not main_content:
                return []
            
            # Get the document title
            document_title = self._get_chapter_title(soup, "pep8", 0)
            
            chunks = []
            chunk_id = 1
            
            # Find all h2 sections (main chapters of PEP 8)
            h2_sections = main_content.find_all('h2')
            
            for i, h2 in enumerate(h2_sections):
                section_title = h2.get_text().strip()
                if not section_title:
                    continue
                
                # Get all siblings after this h2 up to the next h2
                section_content = []
                current = h2.next_sibling
                while current and (not hasattr(current, 'name') or current.name != 'h2'):
                    if hasattr(current, 'name'):
                        if current.name == 'section':
                            # Add all children of the section
                            section_content.extend(list(current.children))
                        elif current.get_text().strip():
                            section_content.append(current)
                    current = current.next_sibling
                
                # Remove empty/whitespace-only elements
                section_content = [el for el in section_content if hasattr(el, 'get_text') and el.get_text().strip()]
                
                if not section_content:
                    continue
                
                # Extract text from this section (including h3 subsections)
                section_text = self._extract_clean_text_from_elements(section_content)
                
                if not section_text.strip():
                    continue
                
                # Create chunks for this section
                section_chunks = self._create_chunks_with_overlap(
                    section_text,
                    section_title,
                    chunk_id,
                    "pep8",
                    url
                )
                chunks.extend(section_chunks)
                chunk_id += len(section_chunks)
            
            return chunks
            
        except Exception as e:
            print(f"Error scraping PEP 8: {e}")
            return []
    
    def _scrape_single_page(self, url: str, source_type: str, chapter_num: int) -> List[Dict[str, str]]:
        """Scrape a single HTML page and chunk it by page/chapter."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get the main content area - focus on the actual content
            main_content = self._get_main_content(soup, source_type)
            
            if not main_content:
                return []
            
            # Get the chapter title
            chapter_title = self._get_chapter_title(soup, source_type, chapter_num)
            
            # Extract all text content (without section prefixes)
            full_text = self._extract_clean_text(main_content)
            
            if not full_text.strip():
                return []
            
            # Create chunks with overlap for the entire page
            chunks = self._create_chunks_with_overlap(
                full_text,
                chapter_title,
                1,  # Start chunk ID
                source_type,
                url
            )
            
            return chunks
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return []
    
    def _get_main_content(self, soup, source_type: str):
        """Extract only the main content area, avoiding navigation, header, footer."""
        if source_type == "pep8":
            # For PEP 8, look for the main content area
            # PEP 8 typically has the content in the body, but we need to avoid the sidebar
            main_content = soup.find('body')
            if main_content:
                # Remove navigation sidebar, header, footer if present
                for nav in main_content.find_all(['nav', 'header', 'footer', 'aside', 'sidebar']):
                    nav.decompose()
                
                # PEP 8 might have a specific content area - look for it
                content_area = main_content.find('div', class_='content') or main_content.find('div', class_='main') or main_content.find('main')
                if content_area:
                    return content_area
                
                return main_content
        else:
            # For Think Python, look for the main content area
            # Think Python typically has content in a specific container
            # Try to find the main content area by looking for common patterns
            
            # Remove navigation sidebar, header, footer
            for element in soup.find_all(['nav', 'header', 'footer', 'aside', 'sidebar']):
                element.decompose()
            
            # Look for the main content area
            # Think Python often has content in a specific div or the body
            main_content = soup.find('div', class_='content') or soup.find('div', class_='main') or soup.find('main')
            
            if not main_content:
                # If no specific content area found, use body but be more selective
                body = soup.find('body')
                if body:
                    # Remove any remaining navigation-like elements
                    for element in body.find_all(['nav', 'header', 'footer', 'aside', 'sidebar', 'menu']):
                        element.decompose()
                    main_content = body
            
            return main_content
    
    def _get_chapter_title(self, soup, source_type: str, chapter_num: int) -> str:
        """Get the actual chapter title from the page."""
        if source_type == "pep8":
            # For PEP 8, look for the main title
            title_elem = soup.find('h1') or soup.find('title')
            if title_elem:
                return title_elem.get_text().strip()
            return "PEP 8 Style Guide"
        else:
            # For Think Python, only use h1 as chapter title
            h1_elem = soup.find('h1')
            if h1_elem:
                title = h1_elem.get_text().strip()
                # Clean up the title
                title = re.sub(r'^\d+\.\s*', '', title)  # Remove chapter numbers
                return title
            return f"Chapter {chapter_num}"
    
    def _extract_clean_text(self, content_element) -> str:
        """Extract clean text without repetitive section prefixes."""
        text_parts = []
        
        # For Think Python, we want to extract all content except h1 (which is the chapter title)
        # For PEP 8, we can extract all content
        for element in content_element.find_all(['p', 'pre', 'ul', 'ol', 'blockquote', 'h2', 'h3', 'h4', 'h5', 'h6']):
            if element.name == 'pre':
                # Preserve code blocks
                text_parts.append(f"\n```\n{element.get_text()}\n```\n")
            elif element.name == 'p':
                # Regular paragraphs
                text_parts.append(element.get_text().strip())
            elif element.name in ['ul', 'ol']:
                # Lists
                for li in element.find_all('li'):
                    text_parts.append(f"• {li.get_text().strip()}")
            elif element.name == 'blockquote':
                # Blockquotes
                text_parts.append(f"> {element.get_text().strip()}")
            elif element.name in ['h2', 'h3', 'h4', 'h5', 'h6']:
                # Include subsection headers as part of the text flow
                text_parts.append(f"\n{element.get_text().strip()}\n")
        
        return " ".join(text_parts)
    
    def _extract_clean_text_from_elements(self, elements) -> str:
        """Extract clean text from a list of elements."""
        text_parts = []
        
        for element in elements:
            if element.name == 'pre':
                # Preserve code blocks
                text_parts.append(f"\n```\n{element.get_text()}\n```\n")
            elif element.name == 'p':
                # Regular paragraphs
                text_parts.append(element.get_text().strip())
            elif element.name in ['ul', 'ol']:
                # Lists
                for li in element.find_all('li'):
                    text_parts.append(f"• {li.get_text().strip()}")
            elif element.name == 'blockquote':
                # Blockquotes
                text_parts.append(f"> {element.get_text().strip()}")
            elif element.name in ['h2', 'h3', 'h4', 'h5', 'h6']:
                # Include subsection headers as part of the text flow
                text_parts.append(f"\n{element.get_text().strip()}\n")
        
        return " ".join(text_parts)
    
    def _create_chunks_with_overlap(
        self, 
        text: str, 
        chapter_title: str, 
        start_chunk_id: int,
        source_type: str,
        url: str
    ) -> List[Dict[str, str]]:
        """Create chunks with overlap from the full page text."""
        chunks = []
        
        # Add chapter title prefix to the text
        text_with_title = f"[Chapter: {chapter_title}]\n\n{text}"
        
        if len(text_with_title) <= self.max_chunk_length:
            # Single chunk
            chunks.append({
                "section_name": chapter_title,
                "text": text_with_title,
                "chunk_id": start_chunk_id,
                "source_type": source_type,
                "url": url,
                "is_overlap": False
            })
        else:
            # Split into multiple chunks with overlap
            words = text.split()
            current_chunk = ""
            chunk_id = start_chunk_id
            
            for i, word in enumerate(words):
                if len(current_chunk + " " + word) <= self.max_chunk_length - len(f"[Chapter: {chapter_title}]\n\n"):
                    current_chunk += " " + word if current_chunk else word
                else:
                    if current_chunk:
                        chunk_text = f"[Chapter: {chapter_title}]\n\n{current_chunk.strip()}"
                        chunks.append({
                            "section_name": chapter_title,
                            "text": chunk_text,
                            "chunk_id": chunk_id,
                            "source_type": source_type,
                            "url": url,
                            "is_overlap": False
                        })
                        chunk_id += 1
                        
                        # Create overlap by keeping last few words
                        overlap_words = current_chunk.split()[-self.overlap_length//10:]  # Approximate
                        current_chunk = " ".join(overlap_words) + " " + word
                    else:
                        current_chunk = word
            
            # Add the last chunk
            if current_chunk:
                chunk_text = f"[Chapter: {chapter_title}]\n\n{current_chunk.strip()}"
                chunks.append({
                    "section_name": chapter_title,
                    "text": chunk_text,
                    "chunk_id": chunk_id,
                    "source_type": source_type,
                    "url": url,
                    "is_overlap": False
                })
        
        return chunks


def save_chunks_to_file(chunks: List[Dict[str, str]], filename: str):
    """Save chunks to a text file for inspection."""
    with open(filename, 'w', encoding='utf-8') as f:
        for chunk in chunks:
            f.write(f"Source: {chunk['source_type']}\n")
            f.write(f"Section: {chunk['section_name']}\n")
            f.write(f"Chunk ID: {chunk['chunk_id']}\n")
            f.write(f"URL: {chunk['url']}\n")
            f.write(f"Text: {chunk['text']}\n")
            f.write("-" * 80 + "\n\n") 