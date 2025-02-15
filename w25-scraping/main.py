from scrapybara import Scrapybara
from scrapybara.anthropic import Anthropic
from scrapybara.tools import BashTool, ComputerTool, EditTool, BrowserTool
from scrapybara.prompts import UBUNTU_SYSTEM_PROMPT
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
import os

load_dotenv()


# Define schemas for structured output
class Company(BaseModel):
    name: str
    description: str
    tags: List[str]


class Companies(BaseModel):
    companies: List[Company]


class ContactInfo(BaseModel):
    contact_method: str
    contact_details: str


def handle_step(step):
    print(f"\nStep output: {step.text}")
    if step.tool_calls:
        for call in step.tool_calls:
            print(f"Tool used: {call.tool_name}")
    if step.usage:
        print(f"Tokens used: {step.usage.total_tokens}")


def main():
    client = Scrapybara(
        api_key=os.getenv("SCRAPYBARA_API_KEY", "YOUR_API_KEY"),
        timeout=600,
    )

    # 1. Start instance
    instance = client.start_ubuntu()
    instance.browser.start()

    try:
        # Set up tools and model
        tools = [
            BashTool(instance),
            ComputerTool(instance),
            EditTool(instance),
            BrowserTool(instance),
        ]
        model = Anthropic()

        # 2. Scrape W25 companies
        companies_response = client.act(
            model=model,
            tools=tools,
            system=UBUNTU_SYSTEM_PROMPT,
            prompt="Go to https://ycombinator.com/companies, set batch filter to W25, and scrape all W25 companies, don't evaluate any code, just look at the HTML and return structured data.",
            schema=Companies,
            on_step=handle_step,
        )
        print(f"\nScraped W25 companies: {companies_response.output.companies}")

        COMPANY_LIMIT = 3
        companies = companies_response.output.companies[:COMPANY_LIMIT]

        # 3. Find best way to contact each company
        for company in companies:
            print(f"\nFinding contact info for {company.name}...")
            contact_response = client.act(
                model=model,
                tools=tools,
                system=UBUNTU_SYSTEM_PROMPT,
                prompt=f"Go to https://ycombinator.com/companies and find the best way to contact YC W25 company {company.name} - {company.description}. Try their website, LinkedIn, and Twitter/X.",
                schema=ContactInfo,
                on_step=handle_step,
            )
            print(f"\nFound contact info for {company.name}: {contact_response.output}")

        # 4. Draft messages for every company
        client.act(
            model=model,
            tools=tools,
            system=UBUNTU_SYSTEM_PROMPT,
            prompt=f"Open LibreOffice, draft a two sentence message to each of the following YC W25 companies, advertising a capybara zoo in Japan: {companies}",
            on_step=handle_step,
        )
        print("\nDrafted messages")

    finally:
        # 5. Clean up
        instance.browser.stop()
        instance.stop()


if __name__ == "__main__":
    main()
