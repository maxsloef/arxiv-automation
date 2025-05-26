import logging
import re
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

from tqdm import tqdm
from modules.api_clients import AnthropicClient
from modules.arxiv import PaperData


def extract_xml_content(text: str) -> Dict[str, Optional[str]]:
    """Extract content using proper XML parsing."""
    tags = ['summary', 'methods', 'contributions', 'limitations']
    results = {tag: None for tag in tags}
    
    # Wrap in root element for valid XML
    wrapped = f"<root>{text}</root>"
    
    try:
        root = ET.fromstring(wrapped)
        for tag in tags:
            element = root.find(f".//{tag}")
            if element is not None and element.text:
                results[tag] = element.text.strip()
    except ET.ParseError as e:
        logging.warning(f"XML parsing failed, falling back to regex: {e}")
        # Fallback to regex if needed
        for tag in tags:
            pattern = f'<{tag}>(.*?)</{tag}>'
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                results[tag] = match.group(1).strip()
    
    return results


def format_summary_html(results: dict[str, Optional[str]]) -> str:
    """
    Format the extracted XML content into HTML.
    
    Args:
        results (Dict[str, Optional[str]]): Dictionary with tag names as keys and content as values
        
    Returns:
        str: HTML formatted string
    """
    html_content = []
    
    for tag, content in results.items():
        if content:
            html_content.append(f"<h3>{tag.capitalize()}</h3>")
            html_content.append(f"<p>{content}</p>")
    
    return "\n".join(html_content)


class PaperSummarizer:
    
    MAX_REQ_BYTES = 32 * 1000000  # 32MB
    MAX_REQ_PAGES = 100

    def __init__(self, client: AnthropicClient, arxiv_client=None):
        self._client = client
        self._arxiv_client = arxiv_client

    def _generate_summary_prompt(self) -> str:
        """
        Generate a prompt for the AI model to summarize a paper.
        
        Returns:
            str: The prompt for the AI model.
        """
        return """
        I'm sharing a research paper with you as a PDF attachment. Please provide a comprehensive summary of this paper.
        
        Please analyze the full PDF and provide:
        
        1. A concise summary (250-300 words) of the paper's main contributions and findings
        2. The key methodologies used
        3. The key contributions
        4. Any notable limitations mentioned
        
        Focus especially on the paper's relevance to interpretability research, mechanistic interpretability, and explainable AI. 

        Output your response in the following XML tags:
        <summary></summary>
        <methods></methods>
        <contributions></contributions>
        <limitations></limitations>

        Plan your response outside of the XML tags before writing the final output.
        """

    def summarize_paper(self, pdf_url: str) -> str:
        """
        Summarize a single paper given its PDF URL.
        
        Args:
            pdf_url (str): URL to the paper's PDF.
        
        Returns:
            str: HTML formatted summary of the paper.
        """
        # Generate prompt for the AI model
        prompt = self._generate_summary_prompt()
        
        # Check if the prompt is too large
        if len(prompt.encode('utf-8')) > self.MAX_REQ_BYTES:
            raise ValueError("Prompt exceeds maximum request size.")
        
        # Send request to the AI model with PDF URL
        response = self._client.send_request(
            prompt=prompt, 
            pdf_url=pdf_url,
            max_tokens_to_sample=5000
        )

        processed_response = extract_xml_content(response)
        return format_summary_html(processed_response)
    
    def _summarize_with_retry(self, paper: PaperData, max_retries: int = 2) -> str:
        """Summarize with retry logic."""
        for attempt in range(max_retries + 1):
            try:
                return self.summarize_paper(paper.pdf_url)
            except Exception as e:
                if attempt == max_retries:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff

    def summarize_papers(self, papers: List[PaperData], max_workers: int = 3) -> List[PaperData]:
        """
        Summarize multiple papers concurrently with caching support.
        
        Args:
            papers (List[PaperData]): List of paper data objects.
            max_workers (int): Maximum number of concurrent workers.
        
        Returns:
            List[PaperData]: List of papers with summaries added.
        """
        summarized_papers = []
        papers_to_summarize = []
        
        # First pass: check cache for existing summaries
        for paper in papers:
            if self._arxiv_client and hasattr(self._arxiv_client, 'is_paper_cached') and self._arxiv_client.is_paper_cached(paper.id):
                # Load from cache
                cached_paper = self._arxiv_client.load_paper_from_cache(paper.id)
                if cached_paper and cached_paper.summary:
                    logging.info(f"Using cached summary for paper {paper.id}")
                    summarized_papers.append(cached_paper)
                    continue
            
            # Paper needs to be summarized
            if paper.pdf_url:
                papers_to_summarize.append(paper)
            else:
                logging.warning(f"Skipping paper {paper.id} - no PDF URL")
        
        # Second pass: summarize papers not in cache (with concurrency)
        if papers_to_summarize:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_paper = {
                    executor.submit(self._summarize_with_retry, paper): paper 
                    for paper in papers_to_summarize
                }
                
                for future in tqdm(as_completed(future_to_paper), total=len(future_to_paper), desc="Summarizing papers"):
                    paper = future_to_paper[future]
                    try:
                        summary = future.result()
                        paper.summary = summary
                        summarized_papers.append(paper)
                        
                        # Cache the paper with summary
                        if self._arxiv_client and hasattr(self._arxiv_client, 'save_paper_to_cache'):
                            self._arxiv_client.save_paper_to_cache(paper)
                            
                    except Exception as e:
                        logging.error(f"Failed to summarize {paper.id}: {e}")
                        
        return summarized_papers