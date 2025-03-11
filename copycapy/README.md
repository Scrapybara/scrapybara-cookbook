# CopyCapy

<img alt="TypeScript" src="https://img.shields.io/badge/TypeScript-blue.svg?logo=TypeScript&logoColor=white" />

Scrape and transform websites into capybara-themed versions with Scrapybara Act SDK and Playwright.

## Features

- HTML + CSS + image scraping with Playwright
- Agentic capybara-themed code generation
- Single-file output with embedded CSS
- Support for dynamically-loaded content

## Prerequisites

- Node.js 18+
- pnpm
- Scrapybara API key (get one at [scrapybara.com](https://scrapybara.com))

## Installation

1. Clone the repository:

```bash
git clone https://github.com/scrapybara/scrapybara-cookbook.git
cd scrapybara-cookbook/copycapy
```

2. Install dependencies:

```bash
pnpm install
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

Start the project with pnpm:

```bash
pnpm start
```

Watch the magic happen with the logged stream URL or on your [Scrapybara dashboard](https://scrapybara.com/dashboard).

By default, CopyCapy will transform Y Combinator's website. To customize which website to capyfy:

1. Open `src/index.ts`
2. Find the line with `new CopyCapy().capyfy("https://ycombinator.com")`
3. Replace the URL with your desired website

For example:

```typescript
new CopyCapy().capyfy("https://example.com");
```

## Project Structure

```
.
├── .env              # Environment variables
├── package.json      # pnpm dependencies and project config
├── README.md         # This file
├── src/
│   └── index.ts      # Main script
└── tsconfig.json     # TypeScript configuration
```
