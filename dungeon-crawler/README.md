# Dungeon Crawler

<img alt="Python" src="https://img.shields.io/badge/Python-blue.svg?logo=Python&logoColor=white" />

Computer-using agent that autonomously plays Dungeon Crawl Stone Soup (DCSS) with Scrapybara Act SDK. The agent creates characters, explores dungeons, fights monsters, and makes strategic decisions in real-time.

DCSS is a really good vibe check for computer use agents and an evaluation on our private CapyBench.

## Features

- Dungeon Crawl Stone Soup (DCSS) installation
- Automatic character creation, game start, and gameplay loop

## Prerequisites

- Python 3.8+
- uv
- Scrapybara API key (get one at [scrapybara.com](https://scrapybara.com))

## Installation

1. Clone the repository:

```bash
git clone https://github.com/Scrapybara/scrapybara-cookbook.git
cd scrapybara-cookbook/dungeon-crawler
```

2. Install dependencies:

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

Watch the agent play with the logged stream URL or on your [Scrapybara dashboard](https://scrapybara.com/dashboard).

The script will launch an Ubuntu instance, install Dungeon Crawl Stone Soup, create a character, and start the game.

## Game Information

[Dungeon Crawl Stone Soup](https://crawl.develz.org/) is a roguelike adventure game where players explore randomly generated dungeons, fight monsters, and attempt to retrieve the Orb of Zot.

## Project Structure

```
.
├── .env              # Environment variables
├── pyproject.toml    # uv dependencies
├── README.md         # This file
└── src/
    └── main.py       # Main script
```
