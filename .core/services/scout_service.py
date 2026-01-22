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
import httpx
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict

# Optional: crawl4ai for advanced scraping
try:
    from crawl4ai import AsyncWebCrawler
    HAS_CRAWL4AI = True
except ImportError:
    HAS_CRAWL4AI = False
    print("[Scout] crawl4ai not installed. Using basic HTTP scraping fallback.")

try:
    from ..config import WORKSPACE_DIR, TAVILY_API_KEY
    from .base_service import BaseAgentService
except ImportError:
    # Fallback/Standalone
    from .core.config import WORKSPACE_DIR, TAVILY_API_KEY
    from .core.services.base_service import BaseAgentService

INCOMING_DIR = os.path.join(WORKSPACE_DIR, "incoming")

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str = "web"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ScrapedContent:
    url: str
    title: str
    content: str
    scraped_at: str
    word_count: int
    checksum: str

class ScoutService(BaseAgentService):
    """
    The Scout Agent: Performs web research and delivers results to the Librarian.
    """
    
    def __init__(self):
        super().__init__(agent_id="scout-1", agent_type="scout", capabilities=["research", "web-scraping", "ingestion"])
        self.web_client = httpx.AsyncClient(timeout=30.0)
        os.makedirs(INCOMING_DIR, exist_ok=True)
        
    async def process_task(self, task: Dict[str, Any]):
        """Process 'research' tasks."""
        # Only process if task text starts with "Research:" or type is research
        topic = task.get("text", "")
        if topic.startswith("Research: "):
            topic = topic.replace("Research: ", "")
            
        print(f"[Scout] Researching: {topic}")
        await self.update_task(task['id'], "in_progress")
        
        try:
            results = await self.research_topic(topic)
            await self.update_task(task['id'], "completed", {"results": results})
        except Exception as e:
            await self.update_task(task['id'], "failed", {"error": str(e)})

    async def search_web(self, query: str, num_results: int = 5) -> List[SearchResult]:
        if TAVILY_API_KEY:
            return await self._search_tavily(query, num_results)
        else:
            return self._simulate_search(query, num_results)
    
    async def _search_tavily(self, query: str, num_results: int) -> List[SearchResult]:
        try:
            resp = await self.web_client.post(
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
        return [
            SearchResult(
                title=f"Result {i+1}: {query}",
                url=f"https://example.com/article-{i+1}",
                snippet=f"Simulated result for '{query}'",
                source="simulated"
            )
            for i in range(min(num_results, 3))
        ]

    async def scrape_url(self, url: str) -> Optional[ScrapedContent]:
        try:
            if HAS_CRAWL4AI:
                return await self._scrape_crawl4ai(url)
            else:
                return await self._scrape_basic(url)
        except Exception as e:
            print(f"[Scout] Failed to scrape {url}: {e}")
            return None

    async def _scrape_crawl4ai(self, url: str) -> Optional[ScrapedContent]:
        # (Assuming crawl4ai usage remains same, create new crawler instance per call)
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
        resp = await self.web_client.get(url, follow_redirects=True)
        resp.raise_for_status()
        content = resp.text
        # Naive extraction
        import re
        text = re.sub(r'<[^>]+>', ' ', content)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return ScrapedContent(
            url=url,
            title="Extracted Content",
            content=text[:10000],
            scraped_at=datetime.utcnow().isoformat(),
            word_count=len(text.split()),
            checksum=hashlib.md5(text.encode()).hexdigest()
        )

    async def save_to_incoming(self, content: ScrapedContent) -> str:
        filename = f"scout_{hashlib.md5(content.url.encode()).hexdigest()[:12]}.md"
        filepath = os.path.join(INCOMING_DIR, filename)
        
        md_content = f"# {content.title}\n\n**Source:** {content.url}\n\n{content.content}"
        
        # Use BaseService client to write file if possible, or direct FS
        # For now, sticking to direct FS as per original
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)
        return filepath

    async def register_source(self, content: ScrapedContent) -> dict:
        try:
             # Using web_client to explicitly hit the API endpoint
             # This bypasses the memory_client abstraction for now to match original behavior
             # of hitting /sources/add directly
             url = f"{self.client.base_url}/sources/add"
             resp = await self.web_client.post(
                url,
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
            print(f"[Scout] Register source failed: {e}")
            return {"error": str(e)}

    async def research_topic(self, topic: str, max_sources: int = 5) -> Dict[str, Any]:
        print(f"[Scout] Researching {topic}...")
        results = await self.search_web(topic, max_sources)
        saved = []
        for res in results:
            if "example.com" in res.url: continue
            content = await self.scrape_url(res.url)
            if content:
                path = await self.save_to_incoming(content)
                saved.append(path)
                await self.register_source(content)
        return {"topic": topic, "saved": saved}

    async def close(self):
        await self.web_client.aclose()
        await super().stop()

if __name__ == "__main__":
    import sys
    topic = sys.argv[1] if len(sys.argv) > 1 else "Test Topic"
    service = ScoutService()
    asyncio.run(service.research_topic(topic))
