# Wide Research

<img alt="Python" src="https://img.shields.io/badge/Python-blue.svg?logo=Python&logoColor=white" />

Deep Research but wide. Scrape YC W25 companies and find the best way to contact each company in parallel batches.

## Features

- Automatically extract YC W25 companies at once
- Parallel batch instance launching and research
- Schema-based data extraction
- Create email drafts with LibreOffice

## Prerequisites

- Python 3.8+
- uv
- Scrapybara API key (get one at [scrapybara.com](https://scrapybara.com))

## Installation

1. Clone the repository:

```bash
git clone https://github.com/Scrapybara/scrapybara-cookbook.git
cd scrapybara-cookbook/wide-research
```

2. Install dependencies with uv:

```bash
uv sync
```

3. Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Then edit `.env` with your API keys:

```bash
SCRAPYBARA_API_KEY=your_api_key_here
```

## Usage

Run the project using uv:

```bash
uv run src/main.py
```

The script will:

1. Start an Browser instance and scrape YC W25 companies (default 25)
2. In batches, launch Browser instances and find contact info for each company (default 5 per batch)
3. Start an Ubuntu instance and create email drafts with LibreOffice

## Project Structure

```
.
├── .env              # Environment variables
├── pyproject.toml    # uv dependencies
├── README.md         # This file
└── src/
    └── main.py       # Main script
```
