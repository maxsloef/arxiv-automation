# arXiv Mechanistic Interpretability Papers

An automated tool that searches for mechanistic interpretability papers on arXiv, summarizes them using Claude, and sends daily email digests.

*(Note: This project, including this README, was assembled through pure vibes and cosmic intuition. I/Claude coded first and asked questions later. The git history reads like jazz improvisation. May the programming gods have mercy on our souls. ✨)*

## Features

- **Specialized Search**: Searches arXiv specifically for mechanistic interpretability papers in AI/ML categories
- **Duplicate Detection**: Tracks previously seen papers to avoid sending duplicates
- **AI Summarization**: Uses Anthropic's Claude to generate comprehensive summaries from paper PDFs
- **Email Digests**: Sends well-formatted HTML emails with paper summaries via SendGrid
- **GitHub Actions Integration**: Automated daily runs at 8:00 AM UTC
- **Manual Execution**: Can be run on-demand for testing

## How It Works

1. Searches arXiv for papers containing "mechanistic interpretability" in CS.AI, CS.LG, and CS.CL categories
2. Filters out previously seen papers (tracked in `seen_papers.json`)
3. Downloads and analyzes PDFs using Claude to extract:
   - Concise summary (250-300 words)
   - Key methodologies
   - Main contributions
   - Notable limitations
4. Sends an HTML-formatted email digest with all summaries

## Setup

### Prerequisites

- Python 3.11+
- Anthropic API key (for Claude)
- SendGrid API key (for email delivery)
- GitHub repository (for automated runs)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/arxiv-automation.git
   cd arxiv-automation
   ```

2. Create a virtual environment:
   ```bash
   python -m venv arxiv-env
   source arxiv-env/bin/activate  # On Windows: arxiv-env\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### GitHub Actions Setup

1. Go to your repository Settings → Secrets and variables → Actions
2. Add the following secrets:
   - `ANTHROPIC_API_KEY`
   - `SENDGRID_API_KEY`
   - `SENDER_EMAIL`
   - `RECIPIENT_EMAIL`

3. The workflow will run automatically at 8:00 AM UTC daily, or can be triggered manually from the Actions tab

## Usage

### Manual Run (Testing)

```bash
python run_once.py
```

This will:
- Search for up to 50 recent mechanistic interpretability papers
- Generate summaries for any new papers found
- Send an email to the configured recipient
- Update `seen_papers.json` to track processed papers

### Automated Daily Runs

The GitHub Actions workflow (`.github/workflows/daily-arxiv.yml`) handles:
- Daily execution at 8:00 AM UTC
- Automatic commit of `seen_papers.json` to track processed papers
- Environment variable management from GitHub Secrets

## Configuration

Edit `config.json` to customize:

```json
{
  "llm_provider": "anthropic",
  "anthropic_model": "claude-opus-4-20250514",
  "max_results": 50,
  "days_back": 1
}
```

Note: The search query is hardcoded for mechanistic interpretability papers. To modify the search terms, edit the `search_interpretability_papers` method in `modules/arxiv.py`.

## Project Structure

```
├── modules/              # Core functionality
│   ├── arxiv.py         # arXiv API client with deduplication
│   ├── api_clients.py   # Anthropic Claude client
│   ├── summarizer.py    # PDF analysis and summarization
│   └── email_sender.py  # SendGrid email formatting/sending
├── run_once.py          # Manual execution script
├── config.py            # Configuration management
├── seen_papers.json     # Tracking file for processed papers
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
└── .github/
    └── workflows/
        └── daily-arxiv.yml  # GitHub Actions workflow
```

## How Summarization Works

The tool sends paper PDFs directly to Claude using Anthropic's document analysis capabilities. For each paper, Claude extracts:

- **Summary**: A comprehensive 250-300 word overview focusing on interpretability aspects
- **Methods**: Key methodologies and techniques used
- **Contributions**: Main contributions to the field
- **Limitations**: Any notable limitations mentioned by the authors

## Troubleshooting

**No papers found**: 
- The tool searches specifically for "mechanistic interpretability" papers
- Check if there are new papers in the last day matching this criteria
- Review `seen_papers.json` - you may need to clear it to reprocess papers

**Email not sending**:
- Verify SendGrid API key and email addresses in `.env`
- Check SendGrid account status and sending limits
- Ensure sender email is verified in SendGrid

**GitHub Actions failing**:
- Check that all required secrets are set in repository settings
- Review the Actions log for specific error messages
- Ensure `seen_papers.json` can be committed (check branch protection rules)

## Notes

- Only new papers are processed - previously seen papers are skipped
- The `seen_papers.json` file is automatically maintained and committed by GitHub Actions
