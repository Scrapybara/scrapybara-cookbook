# Scrapybara CLI

<img alt="Python" src="https://img.shields.io/badge/Python-blue.svg?logo=Python&logoColor=white" />

A command line interface for Scrapybara. Originally created by [@keell0renz](https://github.com/keell0renz).

## Prerequisites

- Python 3.8+
- uv
- Scrapybara API key (get one at [scrapybara.com](https://scrapybara.com))

## Installation

1. Clone the repository:

```bash
git clone https://github.com/Scrapybara/scrapybara-cookbook.git
cd scrapybara-cookbook/scrapybara-cli
```

2. Install dependencies:

```bash
uv sync
```

3. Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

## Usage

The CLI supports two instance types:

- `ubuntu`: Full Ubuntu VM with bash access and browser
- `browser`: Lightweight browser-only instance

Example usage:

```bash
❯ uv run python -m src.main --instance-type browser
Stream URL: ...
> What's the weather like in Tokyo?
```

The CLI will start an interactive session where you can type natural language commands.

## Project Structure

```
.
├── .env              # Environment variables
├── pyproject.toml    # uv dependencies
├── README.md         # This file
└── src/
    ├── agent.py      # Agent logic
    └── main.py       # Main script
```
