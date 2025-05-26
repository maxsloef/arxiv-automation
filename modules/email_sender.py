"""Module for sending email notifications with paper summaries using SendGrid."""

import html
from typing import List
from modules.summarizer import PaperData

class EmailSender:
    """Class for sending email notifications with paper summaries using SendGrid."""

    MAX_EMAIL_SIZE = 10 * 1024 * 1024  # 10MB limit
    
    def __init__(self, api_key: str, sender_email: str):
        """
        Initialize the EmailSender with SendGrid.
        
        Args:
            api_key: SendGrid API key
            sender_email: Sender's email address
        """
        self.api_key = api_key
        self.sender_email = sender_email

    def _escape_html(self, text: str) -> str:
        """Safely escape HTML content."""
        return html.escape(text) if text else ""
    
    def _escape_url(self, url: str) -> str:
        """Safely escape URL for href attribute."""
        if not url:
            return "#"
        
        # Basic validation - ensure it's an arxiv URL
        if not url.startswith(('http://arxiv.org', 'https://arxiv.org')):
            return "#"
        
        # HTML escape the URL to prevent attribute breaking
        return html.escape(url, quote=True)
        
    def _create_html_content(self, paper_summaries: List[PaperData]) -> str:
        """Create HTML content with proper escaping."""
        html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; }
                .paper { margin-bottom: 30px; border-bottom: 1px solid #eee; padding-bottom: 20px; }
                .title { font-size: 18px; font-weight: bold; margin-bottom: 10px; }
                .authors { font-style: italic; margin-bottom: 10px; }
                .published { color: #666; margin-bottom: 10px; }
                .summary { margin-bottom: 15px; }
                .link { color: #0366d6; }
                .keywords { margin-top: 10px; }
                .keyword { background-color: #f1f8ff; padding: 3px 8px; border-radius: 3px; margin-right: 5px; font-size: 12px; }
            </style>
        </head>
        <body>
            <h1>Daily arXiv Interpretability Papers</h1>
        """
        
        for paper in paper_summaries:
            html += f"""
            <div class="paper">
                <div class="title">{self._escape_html(paper.title)}</div>
            """
            
            if paper.authors:
                # Escape each author name individually
                escaped_authors = [self._escape_html(author) for author in paper.authors]
                authors_str = ", ".join(escaped_authors)
                html += f'<div class="authors">Authors: {authors_str}</div>'
                
            if paper.published:
                html += f'<div class="published">Published: {self._escape_html(paper.published)}</div>'
                
            html += f"""
                <div class="summary">{self._escape_html(paper.summary)}</div>
                <div><a class="link" href="{self._escape_url(paper.url)}" target="_blank">Read Paper</a></div>
            """
            
            if paper.keywords:
                html += '<div class="keywords">'
                for keyword in paper.keywords:
                    html += f'<span class="keyword">{self._escape_html(keyword)}</span>'
                html += '</div>'
                
            html += '</div>'
            
        html += """
        </body>
        </html>
        """
        return html
    
    def _create_plain_text_content(self, paper_summaries: List[PaperData]) -> str:
        """
        Create plain text content from paper summaries as a fallback.
        
        Args:
            paper_summaries: List of paper summaries
            
        Returns:
            Plain text content as a string
        """
        text_content = f"Daily arXiv Interpretability Papers\n\n"
        for paper in paper_summaries:
            text_content += f"Title: {paper.title}\n"
            if paper.authors:
                text_content += f"Authors: {', '.join(paper.authors)}\n"
            if paper.published:
                text_content += f"Published: {paper.published}\n"
            text_content += f"Summary: {paper.summary}\n"
            text_content += f"URL: {paper.url}\n\n"
        
        return text_content
        
    def send_email(self, recipient_email: str, subject: str, paper_summaries: List[PaperData]) -> bool:
        """
        Send an email with paper summaries using SendGrid.
        
        Args:
            recipient_email: Recipient's email address
            subject: Email subject
            paper_summaries: List of paper summaries
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            # Import SendGrid here to avoid importing it at module level
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Content, Email
            
            # Create HTML and plain text content
            html_content = self._create_html_content(paper_summaries)
            text_content = self._create_plain_text_content(paper_summaries)
            
            # Create message
            message = Mail(
                from_email=Email(self.sender_email),
                to_emails=recipient_email,
                subject=subject,
                plain_text_content=Content("text/plain", text_content),
                html_content=Content("text/html", html_content)
            )
            
            # Send email using SendGrid
            sg = SendGridAPIClient(self.api_key)
            response = sg.send(message)
            
            # Check response status
            if response.status_code >= 200 and response.status_code < 300:
                print(f"Email sent successfully. Status code: {response.status_code}")
                return True
            else:
                print(f"Failed to send email. Status code: {response.status_code}")
                print(f"Response body: {response.body}")
                return False
                
        except ImportError:
            print("SendGrid package is not installed. Please install it with 'pip install sendgrid'.")
            return False
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False