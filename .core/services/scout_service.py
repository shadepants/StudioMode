"""
Scout Service for Studio Mode
==============================
Autonomous web research agent that gathers information on topics
and feeds results to the Librarian for ingestion into the Knowledge Base.
"""

import os
import json
import hashlib
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict

import httpx

# Optional: crawl4ai for advanced scraping (graceful fallback)
try:
    from crawl4ai import AsyncWebCrawler
    HAS_CRAWL4AI = True
except ImportError:
    HAS_CRAWL4AI = False
    print("[Scout] crawl4ai not installed. Using basic HTTP scraping fallback.")

# --- CONFIGURATION ---
MEMORY_SERVER_URL = os.getenv("MEMORY_SERVER_URL", "http://127.0.0.1:8000")
WORKSPACE_INCOMING = "./workspace/incoming"
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
SERP_API_KEY = os.getenv("SERP_API_KEY", "")


@dataclass
class SearchResult:
    """Represents a single search result."""
    title: str
    url: str
    snippet: str
    source: str = "web"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ScrapedContent:
    """Represents scraped content from a URL."""
    url: str
    title: str
    content: str
    scraped_at: str
    word_count: int
    checksum: str


class ScoutService:
    """
    The Scout Agent: Performs web research and delivers results to the Librarian.
    
    Workflow:
    1. Search for a topic using available search APIs
    2. Scrape top results for content
    3. Save scraped content to workspace/incoming for Librarian ingestion
    4. Register sources with the Memory Server
    """
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.memory_url = MEMORY_SERVER_URL
        os.makedirs(WORKSPACE_INCOMING, exist_ok=True)
    
    async def search_web(self, query: str, num_results: int = 5) -> List[SearchResult]:
        """
        Search the web for information on a topic.
        Tries Tavily first, falls back to basic search simulation.
        """
        if TAVILY_API_KEY:
            return await self._search_tavily(query, num_results)
        else:
            # Fallback: Simulated search for development
            return self._simulate_search(query, num_results)
    
    async def _search_tavily(self, query: str, num_results: int) -> List[SearchResult]:
        """Search using Tavily API."""
        try:
            resp = await self.client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": TAVILY_API_KEY,
                    "query": query,
                    "search_depth": "advanced",
                    "max_results": num_results
                }
            )
            resp.raise_for_status()
            data = resp.json()
            
            results = []
            for item in data.get("results", []):
                results.append(SearchResult(
                    title=item.get("title", "Untitled"),
                    url=item.get("url", ""),
                    snippet=item.get("content", "")[:500],
                    source="tavily"
                ))
            return results
        except Exception as e:
            print(f"[Scout] Tavily search failed: {e}")
            return self._simulate_search(query, num_results)
    
    def _simulate_search(self, query: str, num_results: int) -> List[SearchResult]:
        """Simulated search results for development/testing."""
        return [
            SearchResult(
                title=f"Result {i+1}: {query}",
                url=f"https://example.com/article-{i+1}",
                snippet=f"This is a simulated search result for '{query}'. In production, this would be real content from the web.",
                source="simulated"
            )
            for i in range(min(num_results, 3))
        ]
    
    async def scrape_url(self, url: str) -> Optional[ScrapedContent]:
        """
        Scrape content from a URL.
        Uses crawl4ai if available, otherwise basic HTTP GET.
        """
        try:
            if HAS_CRAWL4AI:
                return await self._scrape_crawl4ai(url)
            else:
                return await self._scrape_basic(url)
        except Exception as e:
            print(f"[Scout] Failed to scrape {url}: {e}")
            return None
    
    async def _scrape_crawl4ai(self, url: str) -> Optional[ScrapedContent]:
        """Scrape using crawl4ai for JavaScript-rendered content."""
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
            if result.success:
                content = result.markdown or result.extracted_content or ""
                return ScrapedContent(
                    url=url,
                    title=result.metadata.get("title", "Untitled") if result.metadata else "Untitled",
                    content=content,
                    scraped_at=datetime.utcnow().isoformat(),
                    word_count=len(content.split()),
                    checksum=hashlib.md5(content.encode()).hexdigest()
                )
        return None
    
    async def _scrape_basic(self, url: str) -> Optional[ScrapedContent]:
        """Basic HTTP scraping fallback."""
        resp = await self.client.get(url, follow_redirects=True)
        resp.raise_for_status()
        
        content = resp.text
        # Basic title extraction
        title = "Untitled"
        if "<title>" in content.lower():
            start = content.lower().find("<title>") + 7
            end = content.lower().find("</title>")
            if end > start:
                title = content[start:end].strip()
        
        # Strip HTML tags (very basic)
        import re
        text = re.sub(r'<[^>]+>', ' ', content)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return ScrapedContent(
            url=url,
            title=title,
            content=text[:10000],  # Limit content size
            scraped_at=datetime.utcnow().isoformat(),
            word_count=len(text.split()),
            checksum=hashlib.md5(text.encode()).hexdigest()
        )
    
    async def save_to_incoming(self, content: ScrapedContent) -> str:
        """Save scraped content to workspace/incoming for Librarian pickup."""
        # Create filename from URL hash
        filename = f"scout_{hashlib.md5(content.url.encode()).hexdigest()[:12]}.md"
        filepath = os.path.join(WORKSPACE_INCOMING, filename)
        
        # Format as markdown
        md_content = f"""# {content.title}

**Source:** {content.url}
**Scraped:** {content.scraped_at}
**Words:** {content.word_count}
**Checksum:** {content.checksum}

---

{content.content}
"""
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)
        
        print(f"[Scout] Saved to: {filepath}")
        return filepath
    
    async def register_source(self, content: ScrapedContent) -> dict:
        """Register the scraped source with the Memory Server."""
        try:
            resp = await self.client.post(
                f"{self.memory_url}/sources/add",
                json={
                    "title": content.title,
                    "type": "web",
                    "url": content.url,
                    "summary": content.content[:500],
                    "tags": ["scout", "auto-ingested"],
                    "checksum": content.checksum
                }
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[Scout] Failed to register source: {e}")
            return {"status": "error", "error": str(e)}
    
    async def research_topic(self, topic: str, max_sources: int = 5) -> Dict[str, Any]:
        """
        Complete research pipeline for a topic.
        
        1. Search the web
        2. Scrape top results
        3. Save to incoming
        4. Register sources
        """
        print(f"[Scout] Starting research on: {topic}")
        
        # Step 1: Search
        results = await self.search_web(topic, max_sources)
        print(f"[Scout] Found {len(results)} search results")
        
        # Step 2 & 3: Scrape and save
        saved_files = []
        registered_sources = []
        
        for result in results:
            if not result.url or result.url.startswith("https://example.com"):
                # Skip simulated results in production
                continue
                
            content = await self.scrape_url(result.url)
            if content:
                filepath = await self.save_to_incoming(content)
                saved_files.append(filepath)
                
                # Step 4: Register
                reg_result = await self.register_source(content)
                registered_sources.append(reg_result)
        
        return {
            "topic": topic,
            "search_results": len(results),
            "scraped": len(saved_files),
            "saved_files": saved_files,
            "registered": len([r for r in registered_sources if r.get("status") == "success"])
        }
    
    async def close(self):
        """Cleanup resources."""
        await self.client.aclose()


# --- CLI INTERFACE ---
async def main():
    """CLI entry point for manual testing."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python scout_service.py <topic>")
        print("Example: python scout_service.py 'React Server Components'")
        return
    
    topic = " ".join(sys.argv[1:])
    scout = ScoutService()
    
    try:
        result = await scout.research_topic(topic)
        print("\n[Scout] Research Complete!")
        print(json.dumps(result, indent=2))
    finally:
        await scout.close()


if __name__ == "__main__":
    asyncio.run(main())
