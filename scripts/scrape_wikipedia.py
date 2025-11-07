#!/usr/bin/env python3
"""
Script to scrape Wikipedia entry for Democratic-Republican Party
and save it as a text file in the data directory.
"""
import os
import sys
import urllib.parse
import requests
from bs4 import BeautifulSoup
from pathlib import Path


def scrape_wikipedia_page(page_title: str) -> str:
    """
    Scrape a Wikipedia page and return its main content as text.
    
    Uses Wikipedia's REST API to get clean plain text content.
    
    Args:
        page_title: The title of the Wikipedia page (URL-encoded if needed)
        
    Returns:
        The main content of the page as a cleaned text string
    """
    # Wikipedia REST API endpoint for plain text (cleaner than HTML)
    api_url = "https://en.wikipedia.org/api/rest_v1/page/summary"
    text_api_url = "https://en.wikipedia.org/api/rest_v1/page/html"
    
    headers = {
        "User-Agent": "PartyBot Wikipedia Scraper (educational purpose) - Contact: williampaul@example.com"
    }
    
    print(f"Fetching Wikipedia page: {page_title}...")
    
    try:
        # First, try to get the page as HTML (more complete content)
        # URL encode the page title
        encoded_title = urllib.parse.quote(page_title.replace(' ', '_'))
        
        response = requests.get(
            f"{text_api_url}/{encoded_title}",
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        
        # Parse HTML to extract main content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(["script", "style", "nav", "header", "footer", "aside", 
                            "table", "figure", "cite", "sup"]):
            element.decompose()
        
        # Find the main article content
        article = soup.find('article') or soup.find('main') or soup.find('body')
        
        if not article:
            raise ValueError("Could not find article content on page")
        
        # Extract text with better formatting
        text = article.get_text(separator='\n', strip=True)
        
        # Clean up the text
        lines = []
        prev_empty = False
        for line in text.split('\n'):
            line = line.strip()
            # Skip empty lines and very short lines (likely navigation/UI elements)
            if line and len(line) > 15:
                # Skip lines that look like navigation or metadata
                if not any(skip in line.lower() for skip in [
                    'jump to', 'edit', 'article', 'talk', 'read', 'view history',
                    'main page', 'contents', 'current events', 'random article'
                ]):
                    lines.append(line)
                    prev_empty = False
            elif not prev_empty and lines:
                # Add a single blank line between paragraphs
                lines.append('')
                prev_empty = True
        
        # Remove trailing empty lines
        while lines and not lines[-1]:
            lines.pop()
        
        content = '\n'.join(lines)
        
        if len(content) < 500:
            raise ValueError(f"Scraped content too short ({len(content)} chars). Page may not exist or be accessible.")
        
        return content
        
    except requests.RequestException as e:
        print(f"Error fetching Wikipedia page: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"HTTP Status: {e.response.status_code}")
            if e.response.status_code == 404:
                print(f"Page '{page_title}' not found. Check the page title.")
        raise
    except Exception as e:
        print(f"Error parsing Wikipedia page: {e}")
        raise


def save_to_file(content: str, filename: str, data_dir: str = "data") -> str:
    """
    Save content to a text file in the data directory.
    
    Args:
        content: The text content to save
        filename: The filename (will be saved as .txt)
        data_dir: The directory to save to
        
    Returns:
        The full path to the saved file
    """
    # Ensure data directory exists
    data_path = Path(data_dir)
    data_path.mkdir(exist_ok=True)
    
    # Create full file path
    filepath = data_path / f"{filename}.txt"
    
    # Write content
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Saved {len(content)} characters to {filepath}")
    return str(filepath)


def main():
    """Main function to scrape and save Wikipedia content."""
    # Wikipedia page title (can be adjusted)
    page_title = "Democratic-Republican Party"
    
    # Output filename
    output_filename = "democratic_republicans_wikipedia"
    
    try:
        # Scrape the page
        content = scrape_wikipedia_page(page_title)
        
        if not content or len(content) < 100:
            print("Warning: Scraped content seems too short. Check the page title.")
            sys.exit(1)
        
        # Save to file
        filepath = save_to_file(content, output_filename)
        
        print(f"\n✅ Successfully scraped and saved Wikipedia content!")
        print(f"📄 File: {filepath}")
        print(f"📊 Content length: {len(content):,} characters")
        print(f"\n💡 To use this in PartyBot:")
        print(f"   1. Restart the application: poetry run python -m app.main")
        print(f"   2. The RAG system will automatically load this file on startup")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

