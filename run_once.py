"""
Script to run the arXiv paper automation once for testing.
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from modules.arxiv import ArxivClient  # Use the improved arXiv client
from modules.api_clients import AnthropicClient
from modules.summarizer import PaperSummarizer
from modules.email_sender import EmailSender
from config import Config

def main():
    """Run the arXiv paper automation once."""
    # Load environment variables from .env file if it exists
    load_dotenv()
    
    # Create configuration
    config = Config()
    
    # Create ArXiv client using the improved client
    arxiv_client = ArxivClient()
    
    # Create Anthropic API client
    api_config = config.get_api_config()
    
    # Check for API key
    if not api_config["api_key"]:
        print("Error: ANTHROPIC_API_KEY not set in environment variables")
        sys.exit(1)
        
    # Create the client
    api_client = AnthropicClient(api_config["model"], api_config["api_key"])
    llm_provider = "anthropic"  # Hardcode to anthropic
    
    # Create paper summarizer
    summarizer = PaperSummarizer(api_client)
    
    # Create email sender
    sendgrid_api_key = os.environ.get("SENDGRID_API_KEY")
    sender_email = os.environ.get("SENDER_EMAIL")
    recipient_email = os.environ.get("RECIPIENT_EMAIL")
    
    if not sendgrid_api_key:
        print("Error: SENDGRID_API_KEY not set in environment variables")
        sys.exit(1)
        
    if not sender_email:
        print("Error: SENDER_EMAIL not set in environment variables")
        sys.exit(1)
        
    if not recipient_email:
        print("Error: RECIPIENT_EMAIL not set in environment variables")
        sys.exit(1)
    
    email_sender = EmailSender(
        api_key=sendgrid_api_key,
        sender_email=sender_email
    )
    
    # Fall back to the specialized interpretability search
    print("Performing specialized interpretability search...")
    specialized_results = arxiv_client.search_interpretability_papers(max_results=50)
    
    if specialized_results:
        print(f"✓ Found {len(specialized_results)} papers with specialized search")
        for i, paper in enumerate(specialized_results):
            print(f"  Paper {i+1}: {paper.title}")
            print(f"    Published: {paper.published}")
            print(f"    PDF URL: {paper.pdf_url}")
            print(f"    Categories: {paper.categories}")
            print()
        
        # Use these results for our test
        search_results = specialized_results
    
    # If we have search results, try to summarize them and send an email
    if search_results:
        print("\nSummarizing papers with Claude using PDFs...")
        paper_summaries = summarizer.summarize_papers(search_results)
        
        if paper_summaries:
            print(f"✓ Successfully summarized {len(paper_summaries)} papers")
            
            # Try to send an email with the summaries
            print(f"\nSending email to {recipient_email}...")
            today = datetime.now().strftime("%Y-%m-%d")
            subject = f"arXiv Interpretability Papers ({today})"
            
            email_success = email_sender.send_email(
                recipient_email=recipient_email,
                subject=subject,
                paper_summaries=paper_summaries
            )
            
            if email_success:
                print("✓ Email sent successfully!")
            else:
                print("✗ Failed to send email")
        else:
            print("✗ Failed to generate paper summaries")
    else:
        print("\nNo papers found to summarize.")
    
    print("Test run completed.")

if __name__ == "__main__":
    main()