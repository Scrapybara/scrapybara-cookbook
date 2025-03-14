from typing import Optional, List
from scrapybara import Scrapybara
from scrapybara.anthropic import Anthropic, BROWSER_SYSTEM_PROMPT as ANTHROPIC_BROWSER_SYSTEM_PROMPT
from scrapybara.openai import OpenAI, BROWSER_SYSTEM_PROMPT as OPENAI_BROWSER_SYSTEM_PROMPT
from scrapybara.tools import ComputerTool
from scrapybara.client import BaseInstance
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
    def __init__(self, scrapybara_api_key: Optional[str] = None):
        load_dotenv()
        self.api_key = scrapybara_api_key or os.getenv("SCRAPYBARA_API_KEY", "YOUR_API_KEY")
        self.client = Scrapybara(api_key=self.api_key)

    def handle_step(self, step, instance: Optional[BaseInstance] = None):
        instance_id = f" [{instance.id}]" if instance else ""
        print(f"₍ᐢ•(ܫ)•ᐢ₎{instance_id}: {step.text}")
        if step.tool_calls:
            for call in step.tool_calls:
                print(f"{call.tool_name}{instance_id} → {', '.join(f'{k}={v}' for k,v in call.args.items())}")

    def extract_companies(self, max_companies: int) -> List[Company]:
        instance = self.client.start_browser()
        print("₍ᐢ•(ܫ)•ᐢ₎ Started Browser instance: ", instance.get_stream_url().stream_url)
        tools = [ComputerTool(instance)]
        
        try:
            companies_response = self.client.act(
                model=Anthropic(),
                tools=tools,
                system=ANTHROPIC_BROWSER_SYSTEM_PROMPT,
                prompt=f"Go to https://ycombinator.com/companies, set batch filter to W25, scroll down, and gather the first {max_companies} W25 companies. After you have seen {max_companies} companies, stop and return the companies with the structured output tool.",
                schema=Companies,
                on_step=lambda step: self.handle_step(step, instance),
            )
            print(f"\nScraped W25 companies: {companies_response.output.companies}")
            return companies_response.output.companies
        finally:
            instance.stop()

    def find_company_contact_info(self, company: Company) -> Optional[ContactInfo]:
        instance = self.client.start_browser()
        print("₍ᐢ•(ܫ)•ᐢ₎ Started Browser instance: ", instance.get_stream_url().stream_url)
        tools = [ComputerTool(instance)]
        
        try:
            print(f"\nFinding contact info for {company.name}...")
            contact_response = self.client.act(
                model=OpenAI(),
                tools=tools,
                system=f"""{OPENAI_BROWSER_SYSTEM_PROMPT}
### Task
You are an expert contact method finder. Navigate to the YC W25 company {company.name} - {company.description}'s page and find a good contact method.
A good contact method can be an email, a demo form, a Discord link, or any other way to reach the company.
After you have found one contact method, you must immediately stop and return the contact info with the structured output tool with the contact method and the contact details.
""",
                prompt=f"Go to https://ycombinator.com/companies/{company.name.lower().replace(' ', '-')} and start finding their contact. DO NOT ASK FOR CONFIRMATION AND ALWAYS RETURN THE CONTACT INFO WITH STRUCTURED OUTPUT.",
                schema=ContactInfo,
                on_step=lambda step: self.handle_step(step, instance),
            )
            print(f"\nFound contact info for {company.name}: {contact_response.output}")
            return contact_response.output
        except Exception as e:
            print(f"Error processing {company.name}: {e}")
            return None
        finally:
            instance.stop()

    async def process_company_batch(self, companies: List[Company], max_workers: int) -> List[Optional[ContactInfo]]:
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            tasks = [
                loop.run_in_executor(executor, self.find_company_contact_info, company)
                for company in companies
            ]
            return await asyncio.gather(*tasks)

    async def find_contact_info(self, companies: List[Company], max_workers: int = 5) -> List[Optional[ContactInfo]]:
        all_contact_infos = []
        
        # Process companies in batches of max_workers size
        for i in range(0, len(companies), max_workers):
            batch = companies[i:i + max_workers]
            print(f"\nProcessing batch {i//max_workers + 1} ({len(batch)} companies)")
            
            batch_results = await self.process_company_batch(batch, max_workers)
            all_contact_infos.extend(batch_results)
            
            print(f"Completed batch {i//max_workers + 1}")
        
        return all_contact_infos

    def save_contact_info(self, companies: List[Company], contact_infos: List[Optional[ContactInfo]]):
        """Save the collected contact information to a markdown file with timestamp."""
        from datetime import datetime
        import os

        # Create output directory if it doesn't exist
        os.makedirs("output", exist_ok=True)

        # Generate timestamp for the filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"output/contact_info_{timestamp}.md"

        with open(filename, "w") as f:
            f.write("# YC W25 Company Contact Information\n")
            f.write(f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")

            for company, contact_info in zip(companies, contact_infos):
                f.write(f"## {company.name}\n")
                f.write(f"**Description:** {company.description}\n")
                f.write(f"**Tags:** {', '.join(company.tags)}\n")
                if contact_info is not None:
                    f.write(f"**Contact Method:** {contact_info.contact_method}\n")
                    f.write(f"**Contact Details:** {contact_info.contact_details}\n")
                else:
                    f.write("**Status:** Failed to retrieve contact information\n")
                f.write("\n")

        print(f"\n₍ᐢ•(ܫ)•ᐢ₎ Saved contact information to {filename}")

async def main():
    agent = WideResearch()
    max_companies = 20
    max_parallel_instances = 4

    try:
        # Extract companies
        companies = agent.extract_companies(max_companies)
        
        # Run contact info search in parallel batches
        contact_infos = await agent.find_contact_info(companies, max_parallel_instances)
        print("\nAll contact info gathered:", contact_infos)
        
        # Save contact information to file
        agent.save_contact_info(companies, contact_infos)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
