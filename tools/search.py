from typing import Dict, Any, List, Optional
import requests
import json
from .tool_registry import BaseTool
from utils.logger import get_logger
from config.config import get_config

logger = get_logger(__name__)

class SearchResult:
    """Class to hold search result data."""
    
    def __init__(self, title: str, link: str, snippet: str):
        self.title = title
        self.link = link
        self.snippet = snippet
    
    def __str__(self) -> str:
        return f"Title: {self.title}\nURL: {self.link}\nSnippet: {self.snippet}"
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "title": self.title,
            "link": self.link,
            "snippet": self.snippet
        }

class SearchTool(BaseTool):
    """Tool for searching the web using serper.dev API."""
    
    def __init__(self):
        """Initialize the search tool."""
        super().__init__(
            name="search",
            description="Searches the web using the serper.dev Google Search API"
        )
        self.config = get_config()
        self.api_key = self.config.get("serper_api_key")
        self.base_url = "https://google.serper.dev/search"
    
    def execute(self, parameters: Dict[str, Any], memory: Any) -> Dict[str, Any]:
        """
        Execute a web search with the given parameters, optimized for educational content.
        
        Args:
            parameters (dict): Parameters for the search
                - query (str): Search query string
                - num_results (int, optional): Number of results to return (default: 10)
            memory (Memory): Agent's memory
            
        Returns:
            dict: Search results with metadata
        """
        query = parameters.get("query")
        if not query:
            return {"error": "No search query provided"}
        
        num_results = int(parameters.get("num_results", self.config.get("max_search_results", 10)))
        
        # Enhance query for educational content if applicable
        enhanced_query = self._enhance_educational_query(query)
        
        logger.info(f"Searching for (enhanced): {enhanced_query}")
        
        try:
            # First try with enhanced query
            results = self._search(enhanced_query, num_results)
            
            # If we don't get enough results, try original query
            if len(results) < 3 and enhanced_query != query:
                logger.info(f"Insufficient results with enhanced query, trying original: {query}")
                original_results = self._search(query, num_results)
                # Combine results, prioritizing enhanced query results
                seen_links = {r.link for r in results}
                for result in original_results:
                    if result.link not in seen_links and len(results) < num_results:
                        results.append(result)
                        seen_links.add(result.link)
            
            # Prioritize Kenyan educational sources
            results = self._prioritize_kenyan_sources(results)
            
            # Cache results in memory
            memory.cache_web_content(
                url=f"search:{enhanced_query}",
                content=json.dumps([r.to_dict() for r in results]),
                metadata={"query": enhanced_query, "original_query": query, "count": len(results)}
            )
            
            # Format results for output
            formatted_results = {
                "query": enhanced_query,
                "original_query": query,
                "result_count": len(results),
                "results": [r.to_dict() for r in results]
            }
            
            return formatted_results
        
        except Exception as e:
            error_message = f"Error performing search: {str(e)}"
            logger.error(error_message)
            return {"error": error_message}
    
    def _enhance_educational_query(self, query: str) -> str:
        """Enhance search query for educational content and Kenyan context."""
        query_lower = query.lower()
        
        # Check if it's already well-formed
        if any(term in query_lower for term in ["site:", "filetype:", "inurl:"]):
            return query
        
        # Educational enhancement patterns
        enhanced_terms = []
        
        # Add educational context if not present
        if not any(term in query_lower for term in ["education", "teaching", "curriculum", "lesson"]):
            if any(term in query_lower for term in ["kenya", "kenyan", "nairobi", "mombasa"]):
                enhanced_terms.append("education")
        
        # Add Kenya context for educational queries
        if any(term in query_lower for term in ["lesson", "curriculum", "teaching", "student"]) and \
           not any(term in query_lower for term in ["kenya", "kenyan", "east africa"]):
            enhanced_terms.append("Kenya")
        
        # Subject-specific enhancements
        if "business studies" in query_lower:
            enhanced_terms.extend(["curriculum", "examples"])
        elif "geography" in query_lower and "kenya" in query_lower:
            enhanced_terms.extend(["physical geography", "human geography"])
        elif "mathematics" in query_lower:
            enhanced_terms.extend(["examples", "problems"])
        
        # Construct enhanced query
        if enhanced_terms:
            return f"{query} {' '.join(enhanced_terms)}"
        
        return query
    
    def _prioritize_kenyan_sources(self, results: List[SearchResult]) -> List[SearchResult]:
        """Prioritize results from Kenyan educational sources."""
        kenyan_domains = [
            "kicd.ac.ke", "uon.ac.ke", "ku.ac.ke", "moi.ac.ke", "tukenya.ac.ke",
            "kenyatta.ac.ke", "maseno.ac.ke", "mmu.ac.ke", "dkut.ac.ke",
            "nation.africa", "standardmedia.co.ke", "the-star.co.ke",
            "ke.go.ke", "treasury.go.ke", "knbs.or.ke", "centralbank.go.ke",
            "kenya.gov", "kenyaembassy.com"
        ]
        
        kenyan_results = []
        other_results = []
        
        for result in results:
            is_kenyan = any(domain in result.link.lower() for domain in kenyan_domains)
            if is_kenyan:
                kenyan_results.append(result)
            else:
                other_results.append(result)
        
        # Prioritize Kenyan sources but include international sources too
        return kenyan_results + other_results
    
    def _search(self, query: str, num_results: int = 5) -> List[SearchResult]:
        """
        Perform the actual search using serper.dev API.
        
        Args:
            query (str): Search query
            num_results (int): Number of results to return
            
        Returns:
            list: List of SearchResult objects
        """
        if not self.api_key:
            raise ValueError("Serper API key not configured. Please set SERPER_API_KEY.")
        
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        data = {
            "q": query,
            "num": num_results
        }
        
        timeout = self.config.get("timeout", 30)
        response = requests.post(
            self.base_url,
            headers=headers,
            json=data,
            timeout=timeout
        )
        
        if response.status_code != 200:
            raise Exception(f"Search API returned status code {response.status_code}: {response.text}")
        
        # Wrap response.json() in a try/except
        try:
            search_data = response.json()
        except ValueError:
            raise Exception("Received non-JSON response from search API (possibly HTML error page).")
        
        results = []
        
        # Process organic search results
        organic_results = search_data.get("organic", [])
        for result in organic_results[:num_results]:
            title = result.get("title", "No title")
            link = result.get("link", "")
            snippet = result.get("snippet", "No description available")
            
            results.append(SearchResult(title, link, snippet))
        
        return results

def get_page(url: str) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (WebResearchAgent/1.0)"
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 401:
            logger.error(f"401 Unauthorized: {url}")
            return {"error": f"HTTP 401 accessing {url}"}
        response.raise_for_status()
        return {"content": response.text}
    except requests.RequestException as e:
        logger.error(f"HTTP error accessing {url}: {str(e)}")
        return {"error": str(e)}
