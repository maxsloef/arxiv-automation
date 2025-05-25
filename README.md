# arXiv Automation

A Python application that automatically retrieves papers related to AI interpretability from arXiv and sends daily email summaries.

## Features

- Search for papers on arXiv using specific search terms and categories
- Retrieve paper metadata including titles, authors, abstracts, and publication dates
- Summarize papers using AI (Anthropic Claude or OpenAI GPT)
- Send daily email digests with paper summaries and links
- Configurable scheduling for automated retrieval

## Setup

### Prerequisites

- Python 3.7+
- API key for either Anthropic Claude or OpenAI

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/arxiv-automation.git
   cd arxiv-automation
   ```

2. Create a virtual environment:
   ```
   python -m venv arxiv-env
   ```

3. Activate the virtual environment:
   - On macOS/Linux:
     ```
     source arxiv-env/bin/activate
     ```
   - On Windows:
     ```
     arxiv-env\Scripts\activate
     ```

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Create a `.env` file in the project root with your sensitive configuration:
   ```
   # API Keys (choose one based on your preferred provider)
   ANTHROPIC_API_KEY=your_anthropic_api_key
   OPENAI_API_KEY=your_openai_api_key

   # SendGrid Email Configuration
   SENDGRID_API_KEY=your_sendgrid_api_key
   SENDER_EMAIL=your_email@example.com
   RECIPIENT_EMAIL=recipient@example.com
   ```

6. Configure settings in `config.json` if needed (default values are provided).

## Usage

### Running the Application

```
python app.py
```

This will start the scheduler, which will run at the configured time (default: 8:00 AM) to fetch papers, generate summaries, and send an email digest.

### Configuration

The application can be configured through the `config.json` file:

```json
{
  "llm_provider": "anthropic",
  "anthropic_model": "claude-2",
  "openai_model": "gpt-4",
  "search_terms": ["interpretability", "explainability", "xai"],
  "categories": ["cs.AI", "cs.LG", "cs.CL"],
  "max_results": 5,
  "days_back": 1,
  "run_time": "08:00",
  "run_immediately": false
}
```

- `llm_provider`: Choose between "anthropic" or "openai"
- `anthropic_model`/`openai_model`: Model to use for summarization
- `search_terms`: List of terms to search for on arXiv
- `categories`: List of arXiv categories to search in
- `max_results`: Maximum number of papers to retrieve
- `days_back`: Number of days to look back for papers
- `run_time`: Time to run the job daily (HH:MM format)
- `run_immediately`: Whether to run the job immediately on startup

## Structure

- `app.py`: Main application entry point
- `config.py`: Configuration handling
- `modules/`: Core functionality modules
  - `arxiv_client.py`: Client for interacting with the arXiv API
  - `api_clients.py`: Clients for AI providers (Anthropic, OpenAI)
  - `summarizer.py`: Paper summarization functionality
  - `email_sender.py`: Email generation and sending
  - `scheduler.py`: Scheduling of paper retrieval and notifications

## Notes

- The application uses SendGrid for sending emails - you'll need a SendGrid API key
- The application respects arXiv's rate limiting by adding delays between requests
- AI models have token limits, so very large papers may encounter issues with summarization
- The email is sent as both HTML and plain text, with the HTML version offering better formatting