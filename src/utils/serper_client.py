"""Serper API Client for web search"""
import os
import logging
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class SerperClient:
    """Client for Serper API (Google Search)"""
    
    def __init__(self):
        """Initialize Serper client"""
        self.api_key = os.getenv("SERPER_API_KEY")
        if not self.api_key:
            logger.warning("SERPER_API_KEY not found in environment variables")
        
        self.base_url = "https://google.serper.dev"
        self.headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
    
    def search(
        self,
        query: str,
        num_results: int = 5,
        search_type: str = "search"
    ) -> List[Dict[str, Any]]:
        """
        Perform web search using Serper API
        
        Args:
            query: Search query
            num_results: Number of results to return (default: 5)
            search_type: Type of search - 'search', 'news', 'images', etc.
            
        Returns:
            List of search results with title, snippet, link
        """
        if not self.api_key:
            logger.error("Cannot perform search: SERPER_API_KEY not configured")
            return []
        
        try:
            url = f"{self.base_url}/{search_type}"
            payload = {
                "q": query,
                "num": num_results,
                "gl": "jp",  # Geographic location: Japan
                "hl": "ja"   # Language: Japanese
            }
            
            logger.info(f"Searching Serper API: {query}")
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # Extract organic results
            organic_results = data.get("organic", [])
            for result in organic_results[:num_results]:
                results.append({
                    "title": result.get("title", ""),
                    "snippet": result.get("snippet", ""),
                    "link": result.get("link", ""),
                    "position": result.get("position", 0)
                })
            
            logger.info(f"Found {len(results)} search results")
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Serper API: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in Serper search: {e}")
            return []
    
    def search_multiple_queries(
        self,
        queries: List[str],
        num_results_per_query: int = 3
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search multiple queries and return aggregated results
        
        Args:
            queries: List of search queries
            num_results_per_query: Number of results per query
            
        Returns:
            Dictionary mapping query to list of results
        """
        all_results = {}
        
        for query in queries:
            results = self.search(query, num_results=num_results_per_query)
            all_results[query] = results
        
        return all_results


# Global Serper client instance
serper_client = SerperClient()
