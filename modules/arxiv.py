"""Improved module for interacting with arXiv API using the arxiv package."""

from dataclasses import dataclass
import os
import json
import arxiv
from datetime import datetime
from typing import List, Dict, Optional, Set

@dataclass
class PaperData:
    id: str
    title: str
    url: str
    pdf_url: Optional[str] = None
    doi: Optional[str] = None
    comment: Optional[str] = None
    published: Optional[str] = None
    authors: Optional[List[str]] = None
    abstract: Optional[str] = None
    keywords: Optional[List[str]] = None
    summary: Optional[str] = None
    categories: Optional[List[str]] = None

class ArxivClient:
    """A client for interacting with the arXiv API with paper tracking."""
    
    SEEN_PAPERS_FILE = "seen_papers.json"
    
    def __init__(self):
        """Initialize the arXiv client."""
        self.client = arxiv.Client()
        self.seen_papers = self._load_seen_papers()
    
    def _load_seen_papers(self) -> Dict[str, str]:
        """
        Load the list of previously seen papers from disk.
        
        Returns:
            Dict[str, str]: Map of paper ID to last seen date
        """
        if os.path.exists(self.SEEN_PAPERS_FILE):
            try:
                with open(self.SEEN_PAPERS_FILE, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                print(f"Warning: Error reading {self.SEEN_PAPERS_FILE}, starting fresh")
                return {}
        return {}
    
    def _save_seen_papers(self):
        """Save the list of seen papers to disk."""
        try:
            with open(self.SEEN_PAPERS_FILE, 'w') as f:
                json.dump(self.seen_papers, f)
        except IOError as e:
            print(f"Warning: Unable to save seen papers file: {e}")
    
    def mark_papers_as_seen(self, papers: List[Dict]):
        """
        Mark papers as seen to avoid duplicates in future searches.
        
        Args:
            papers: List of paper dictionaries
        """
        current_date = datetime.now().isoformat()
        for paper in papers:
            if paper:
                self.seen_papers[paper.id] = current_date
        self._save_seen_papers()
    
    def search_interpretability_papers(self, max_results: int = 10, request_size: int = 20, timeout_seconds: float = 1.0) -> List[PaperData]:
        """
        Search for interpretability papers, making individual requests and checking for duplicates.
        Continues until we have enough new papers or exhaust the search space.
        
        Args:
            max_results: Maximum number of new papers to return
            request_size: Number of papers to fetch in each request to arXiv
            timeout_seconds: Time to wait between requests to be polite to arXiv
            
        Returns:
            List[PaperData]: List of paper data objects
        """
        import time
        
        # Pre-crafted query for interpretability papers
        query = "(cat:cs.AI OR cat:cs.LG OR cat:cs.CL) AND %22mechanistic interpretability%22"
        print(f"Searching arXiv with query: {query}")
        
        found_papers = []
        seen_in_this_run = set()
        start_index = 0
        consecutive_seen_requests = 0
        max_consecutive_seen = 3  # Stop if we see 3 consecutive requests with all seen papers
        
        while len(found_papers) < max_results and consecutive_seen_requests < max_consecutive_seen:
            print(f"Making request {start_index // request_size + 1} (papers {start_index}-{start_index + request_size - 1})")
            
            # Create a new search for this batch
            search = arxiv.Search(
                query=query,
                max_results=request_size,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending  # Most recent first
            )
            
            # Set the start index for this request
            search.offset = start_index
            
            try:
                # Fetch this batch of papers
                results = list(self.client.results(search))
                
                if not results:
                    print("No more papers available from arXiv")
                    break
                
                # Check if we found any new papers in this batch
                new_papers_in_batch = 0
                
                for paper in results:
                    paper_id = paper.entry_id.split('/')[-1]
                    
                    # Skip if we've already seen this paper before
                    if paper_id in self.seen_papers or paper_id in seen_in_this_run:
                        print(f"Skipping already seen paper: {paper.title}")
                        continue
                    
                    # Convert the paper to our format and add it to the results
                    paper_data = self._convert_result(paper)
                    found_papers.append(paper_data)
                    seen_in_this_run.add(paper_id)
                    new_papers_in_batch += 1
                    
                    print(f"Found new paper: {paper.title}")
                    
                    # Check if we have enough papers
                    if len(found_papers) >= max_results:
                        break
                
                # Track consecutive requests with no new papers
                if new_papers_in_batch == 0:
                    consecutive_seen_requests += 1
                    print(f"No new papers in this batch ({consecutive_seen_requests}/{max_consecutive_seen})")
                else:
                    consecutive_seen_requests = 0
                
                # Move to the next batch
                start_index += request_size
                
                # Wait between requests to be polite to arXiv
                if len(found_papers) < max_results and consecutive_seen_requests < max_consecutive_seen:
                    print(f"Waiting {timeout_seconds} seconds before next request...")
                    time.sleep(timeout_seconds)
                    
            except Exception as e:
                print(f"Error in request: {e}")
                break
        
        print(f"Search completed. Found {len(found_papers)} new papers.")
        
        # Mark all new papers as seen
        self.mark_papers_as_seen(found_papers)
        
        return found_papers
    
    def search(self, search_terms=None, categories=None, max_results=10):
        """
        Search arXiv for papers matching the given criteria.
        
        Args:
            search_terms: Search terms or phrases
            categories: arXiv categories to search in
            max_results: Maximum number of results to return
            
        Returns:
            list: A list of dictionaries containing paper metadata
        """
        # Build a query string in the format from working_interp_search.py
        query_parts = []
        
        # Add categories with OR between them
        if categories:
            if isinstance(categories, list) and len(categories) > 0:
                cats = " OR ".join([f"cat:{cat}" for cat in categories])
                if len(categories) > 1:
                    query_parts.append(f"({cats})")
                else:
                    query_parts.append(cats)
        
        # Add search terms with quotes for exact match if multiple words
        if search_terms:
            if isinstance(search_terms, list):
                terms = []
                for term in search_terms:
                    if " " in term:  # If term contains spaces, use quotes
                        terms.append(f'"{term}"')
                    else:
                        terms.append(term)
                terms_str = " OR ".join(terms)
                query_parts.append(f"({terms_str})")
            else:
                if " " in search_terms:  # If term contains spaces, use quotes
                    query_parts.append(f'"{search_terms}"')
                else:
                    query_parts.append(search_terms)
        
        # Join query parts with AND
        query = " AND ".join(query_parts) if query_parts else ""
        
        print(f"Searching arXiv with query: {query}")
        
        # Create the search object
        search = arxiv.Search(
            query=query,
            max_results=100,  # Fetch more than we need to account for duplicates
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending  # Most recent first
        )
        
        # Fetch results
        results_generator = self.client.results(search)
        
        # Track papers we've found in this search session
        found_papers = []
        seen_in_this_run = set()
        
        # Get up to max_results papers we haven't seen before
        for paper in results_generator:
            paper_id = paper.entry_id.split('/')[-1]
            
            # Skip if we've already seen this paper before
            if paper_id in self.seen_papers or paper_id in seen_in_this_run:
                print(f"Skipping already seen paper: {paper.title}")
                continue
            
            # Convert the paper to our format and add it to the results
            paper_dict = self._convert_result(paper)
            found_papers.append(paper_dict)
            seen_in_this_run.add(paper_id)
            
            # Check if we have enough papers
            if len(found_papers) >= max_results:
                break
        
        # Mark all new papers as seen
        self.mark_papers_as_seen(found_papers)
        
        return found_papers
    
    def get_paper_by_id(self, paper_id):
        """
        Retrieve a specific paper by its arXiv ID.
        
        Args:
            paper_id: The arXiv ID of the paper
            
        Returns:
            dict: A dictionary containing the paper's metadata
        """
        search = arxiv.Search(id_list=[paper_id])
        try:
            result = next(self.client.results(search))
            return self._convert_result(result)
        except StopIteration:
            return None
    
    def get_pdf_url(self, paper_id):
        """
        Get the PDF URL for a paper.
        
        Args:
            paper_id: The arXiv ID of the paper
            
        Returns:
            str: The URL to the PDF
        """
        paper = self.get_paper_by_id(paper_id)
        return paper.pdf_url
        
        raise ValueError(f"Paper with ID {paper_id} not found or has no PDF URL.")
    
    def _convert_result(self, result):
        """
        Convert an arxiv.Result object to a standardized dictionary.
        
        Args:
            result: An arxiv.Result object
            
        Returns:
            dict: A dictionary containing paper metadata
        """
        # Extract the arXiv ID from the entry ID URL
        arxiv_id = result.entry_id.split('/')[-1]
        
        # Get PDF URL and ensure it uses HTTPS
        pdf_url = result.pdf_url if hasattr(result, 'pdf_url') else f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        if pdf_url.startswith('http:'):
            pdf_url = 'https' + pdf_url[4:]

        paper = PaperData(
            id=arxiv_id,
            categories=result.categories,
            title=result.title,
            url=result.entry_id,
            published=result.published.isoformat() if hasattr(result, 'published') else None,
            authors=[author.name for author in result.authors],
            abstract=result.summary,
            keywords=result.categories,
            pdf_url=pdf_url
        )
        
        # Add DOI if available
        if hasattr(result, 'doi'):
            paper.doi = result.doi
        
        # Add comment if available
        if hasattr(result, 'comment'):
            paper.comment = result.comment
            
        return paper