import requests
from bs4 import BeautifulSoup
from rag_microservice.unified_scraper import UnifiedWebScraper

def debug_pep8_structure():
    url = "https://peps.python.org/pep-0008/"
    
    print("Fetching PEP 8 page...")
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    print("\n=== DEBUGGING PEP 8 STRUCTURE ===")
    
    # Check what h2 elements exist
    all_h2 = soup.find_all('h2')
    print(f"Found {len(all_h2)} h2 elements:")
    for i, h2 in enumerate(all_h2):
        print(f"  {i+1}. {h2.get_text().strip()}")
    
    # Check the main content area
    print("\n=== MAIN CONTENT AREA ===")
    main_content = soup.find('body')
    if main_content:
        # Remove navigation elements
        for nav in main_content.find_all(['nav', 'header', 'footer', 'aside', 'sidebar']):
            nav.decompose()
        
        # Look for content area
        content_area = main_content.find('div', class_='content') or main_content.find('div', class_='main') or main_content.find('main')
        if content_area:
            main_content = content_area
        
        h2_in_content = main_content.find_all('h2')
        print(f"Found {len(h2_in_content)} h2 elements in main content:")
        for i, h2 in enumerate(h2_in_content):
            print(f"\n  {i+1}. {h2.get_text().strip()}")
            # Print all siblings until next h2
            current = h2.next_sibling
            h3_count = 0
            idx = 0
            while current and (not hasattr(current, 'name') or current.name != 'h2'):
                idx += 1
                if hasattr(current, 'name'):
                    print(f"    Sibling {idx}: <{current.name}>")
                    if current.name == 'h3':
                        h3_count += 1
                else:
                    # It's likely a NavigableString (whitespace, newline, etc.)
                    print(f"    Sibling {idx}: type={type(current).__name__}")
                current = current.next_sibling
            print(f"    -> Found {h3_count} h3 subsections in this section.")
    
    print("\n=== TESTING SCRAPER ===")
    scraper = UnifiedWebScraper()
    chunks = scraper.scrape_pep8()
    print(f"Scraper extracted {len(chunks)} chunks")
    
    # Show first few chunks
    for i, chunk in enumerate(chunks[:5]):
        print(f"\nChunk {i+1}:")
        print(f"  Section: {chunk['section']}")
        print(f"  Text preview: {chunk['text'][:200]}...")

if __name__ == "__main__":
    debug_pep8_structure() 