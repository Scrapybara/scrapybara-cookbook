# Scrapybara Cookbook 🥄🥘

A comprehensive collection of examples and recipes for using Scrapybara - the virtual desktop platform for AI agents. This cookbook demonstrates how to create AI assistants that can interact with virtual desktops for automation tasks.

## 🌟 Features

- **AI-Powered Desktop Control**: Build assistants that can interact with GUI applications
- **Claude Integration**: Ready-to-use examples with Anthropic's Claude API
- **Virtual Desktop Automation**: Control browsers, office suites, and system tools
- **Structured Tools**: Modular approach using ComputerTool, BashTool, and EditTool

## 📚 Available Examples

### 🔍 Market Research Assistant

A complete example showing how to:

- Launch and control Firefox for web research
- Take organized notes using LibreOffice Writer
- Create summary spreadsheets in LibreOffice Calc
- Manage files and documents systematically
- Integrate with Claude for intelligent automation

## 🚀 Getting Started

1. Clone this repository:

   ```bash
   git clone https://github.com/yourusername/scrapybara-cookbook.git
   cd scrapybara-cookbook
   ```

2. Install dependencies using Poetry:

   ```bash
   poetry install
   ```

3. Set up your environment variables:

   ```bash
   export SCRAPYBARA_API_KEY='your-scrapybara-api-key'
   export ANTHROPIC_API_KEY='your-anthropic-api-key'
   ```

4. Run the market research example:
   ```bash
   poetry run python examples/market_research.py
   ```

## 📖 Project Structure

```
scrapybara-cookbook/
├── README.md           # Project documentation
├── pyproject.toml      # Poetry dependencies and configuration
└── examples/           # Example scripts
    └── market_research.py
```

## 🛠️ Dependencies

- Python 3.11+
- Scrapybara ^0.1.12
- python-dotenv ^1.0.1
- Anthropic Claude API access

## 🤝 Contributing

We welcome contributions! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📫 Contact

- Website: [scrapybara.com](https://scrapybara.com)
- Twitter: [@ScrapybaraAI](https://x.com/scrapybara)
- Email: hello@scrapybara.com
