from typing import Optional, List
from scrapybara import Scrapybara
from scrapybara.anthropic import Anthropic, UBUNTU_SYSTEM_PROMPT, BROWSER_SYSTEM_PROMPT
from scrapybara.tools import ComputerTool, BashTool
from scrapybara.types import Model
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

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

class WideResearch:
    def __init__(self, model: Model, scrapybara_api_key: Optional[str] = None):
        load_dotenv()
        self.model = model
        self.api_key = scrapybara_api_key or os.getenv("SCRAPYBARA_API_KEY", "YOUR_API_KEY")
        self.client = Scrapybara(api_key=self.api_key)

    def handle_step(self, step):
        print(f"₍ᐢ•(ܫ)•ᐢ₎: {step.text}")
        if step.tool_calls:
            for call in step.tool_calls:
                print(f"{call.tool_name} → {', '.join(f'{k}={v}' for k,v in call.args.items())}")

    def extract_companies(self, max_companies: int) -> List[Company]:
        instance = self.client.start_browser()
        print("₍ᐢ•(ܫ)•ᐢ₎ Started Browser instance: ", instance.get_stream_url().stream_url)
        tools = [ComputerTool(instance)]
        
        try:
            companies_response = self.client.act(
                model=self.model,
                tools=tools,
                system=BROWSER_SYSTEM_PROMPT,
                prompt=f"Go to https://ycombinator.com/companies, set batch filter to W25, and extract ONLY the first {max_companies} W25 companies. Stop when you have seen {max_companies} companies.",
                schema=Companies,
                on_step=self.handle_step,
            )
            print(f"\nScraped W25 companies: {companies_response.output.companies}")
            return companies_response.output.companies
        finally:
            instance.stop()

    def find_company_contact_info(self, company: Company) -> ContactInfo:
        instance = self.client.start_browser()
        print("₍ᐢ•(ܫ)•ᐢ₎ Started Browser instance: ", instance.get_stream_url().stream_url)
        tools = [ComputerTool(instance)]
        
        try:
            print(f"\nFinding contact info for {company.name}...")
            contact_response = self.client.act(
                model=self.model,
                tools=tools,
                system=BROWSER_SYSTEM_PROMPT,
                prompt=f"Go to https://ycombinator.com/companies and find the best way to contact YC W25 company {company.name} - {company.description}. Try their website, LinkedIn, and Twitter/X.",
                schema=ContactInfo,
                on_step=self.handle_step,
            )
            print(f"\nFound contact info for {company.name}: {contact_response.output}")
            return contact_response.output
        finally:
            instance.stop()

    async def process_company_batch(self, companies: List[Company], max_workers: int) -> List[ContactInfo]:
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            tasks = [
                loop.run_in_executor(executor, self.find_company_contact_info, company)
                for company in companies
            ]
            return await asyncio.gather(*tasks)

    async def find_contact_info(self, companies: List[Company], max_workers: int = 5) -> List[ContactInfo]:
        all_contact_infos = []
        
        # Process companies in batches of max_workers size
        for i in range(0, len(companies), max_workers):
            batch = companies[i:i + max_workers]
            print(f"\nProcessing batch {i//max_workers + 1} ({len(batch)} companies)")
            
            batch_results = await self.process_company_batch(batch, max_workers)
            all_contact_infos.extend(batch_results)
            
            print(f"Completed batch {i//max_workers + 1}")
        
        return all_contact_infos

    def draft_messages(self, companies: List[Company]):
        # Start Ubuntu instance to use LibreOffice
        instance = self.client.start_ubuntu()
        print("₍ᐢ•(ܫ)•ᐢ₎ Started Ubuntu instance: ", instance.get_stream_url().stream_url)
        tools = [BashTool(instance), ComputerTool(instance)]
        
        try:
            self.client.act(
                model=self.model,
                tools=tools,
                system=UBUNTU_SYSTEM_PROMPT,
                prompt=f"Open LibreOffice, draft a two sentence message to each of the following YC W25 companies, advertising a capybara zoo in Japan: {companies}",
                on_step=self.handle_step,
            )
            print("\nDrafted messages")
        finally:
            instance.stop()

async def main():
    model = Anthropic()
    agent = WideResearch(model=model)
    max_companies = 25
    max_parallel_instances = 5

    try:
        # Extract companies
        companies = agent.extract_companies(max_companies)
        
        # Run contact info search in parallel batches
        contact_infos = await agent.find_contact_info(companies, max_parallel_instances)
        print("\nAll contact info gathered:", contact_infos)
        
        # Draft messages
        agent.draft_messages(companies)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
