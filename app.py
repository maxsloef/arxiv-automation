"""
Main application for arXiv paper automation.
Retrieves papers related to interpretability from arXiv and sends daily email summaries.
"""

import os
import sys
import time
from dotenv import load_dotenv
from modules.arxiv import ArxivClient
from modules.api_clients import AnthropicClient, OpenAIClient
from modules.summarizer import PaperSummarizer
from modules.email_sender import EmailSender
from config import Config

def create_api_client(config):
    """Create API client based on configuration."""
    api_config = config.get_api_config()
    
    if config["llm_provider"].lower() == "anthropic":
        if not api_config["api_key"]:
            print("Error: ANTHROPIC_API_KEY not set in environment variables")
            sys.exit(1)
        return AnthropicClient(api_config["model"], api_config["api_key"])
    
    elif config["llm_provider"].lower() == "openai":
        if not api_config["api_key"]:
            print("Error: OPENAI_API_KEY not set in environment variables")
            sys.exit(1)
        return OpenAIClient(api_config["model"], api_config["api_key"])
    
    else:
        raise ValueError(f"Unsupported LLM provider: {config['llm_provider']}")

def create_email_sender(config):
    """Create email sender based on configuration."""
    # Get SendGrid API key from environment
    sendgrid_api_key = os.environ.get("SENDGRID_API_KEY")
    sender_email = os.environ.get("SENDER_EMAIL")
    recipient_email = os.environ.get("RECIPIENT_EMAIL")
    
    # Check if required settings are provided
    if not sendgrid_api_key:
        print("Error: SENDGRID_API_KEY not set in environment variables")
        sys.exit(1)
        
    if not sender_email:
        print("Error: SENDER_EMAIL not set in environment variables")
        sys.exit(1)
        
    if not recipient_email:
        print("Error: RECIPIENT_EMAIL not set in environment variables")
        sys.exit(1)
    
    return EmailSender(
        api_key=sendgrid_api_key,
        sender_email=sender_email
    )

def main():
    """Main function to set up and run the arXiv paper automation."""
    # Load environment variables from .env file if it exists
    load_dotenv()
    
    # Create configuration
    config = Config()
    
    # Create ArXiv client
    arxiv_client = ArxivClient()
    
    # Create API client
    api_client = create_api_client(config)
    
    # Create paper summarizer
    summarizer = PaperSummarizer(api_client)
    
    # Create email sender
    email_sender = create_email_sender(config)
    
    # Get arXiv and scheduler configurations
    arxiv_config = config.get_arxiv_config()
    scheduler_config = config.get_scheduler_config()
    email_config = config.get_email_config()
    
    # Create and start the scheduler
    scheduler = PaperScheduler(
        arxiv_client=arxiv_client,
        summarizer=summarizer,
        email_sender=email_sender,
        recipient_email=email_config["recipient_email"],
        search_terms=arxiv_config["search_terms"],
        categories=arxiv_config["categories"],
        max_results=arxiv_config["max_results"],
        days_back=arxiv_config["days_back"]
    )
    
    print("Starting arXiv paper automation...")
    print(f"Using LLM provider: {config['llm_provider']}")
    print(f"Search terms: {arxiv_config['search_terms']}")
    print(f"Categories: {arxiv_config['categories']}")
    print(f"Emails will be sent to: {email_config['recipient_email']}")
    
    try:
        scheduler.start(
            run_time=scheduler_config["run_time"],
            run_immediately=scheduler_config["run_immediately"]
        )
        
        # Keep the main thread running
        while True:
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("\nStopping scheduler...")
        scheduler.stop()
        print("Scheduler stopped. Exiting...")
        sys.exit(0)

if __name__ == "__main__":
    main()