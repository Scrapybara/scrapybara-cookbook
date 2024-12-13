import asyncio
import os
from typing import List, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(".env.example")

from anthropic import Anthropic
from anthropic.types.beta import BetaToolResultBlockParam, BetaMessageParam

from scrapybara import Scrapybara
from scrapybara.anthropic import BashTool, ComputerTool, EditTool, ToolResult

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
SCRAPYBARA_API_KEY = os.getenv("SCRAPYBARA_API_KEY")

SYSTEM_PROMPT = f"""<SYSTEM_CAPABILITY>
* You are utilising an Ubuntu virtual machine using linux architecture with internet access.
* You can feel free to install Ubuntu applications with your bash tool. Use curl instead of wget.
* To open chromium, please just click on the web browser icon or use the "(DISPLAY=:1 chromium --no-sandbox &)" command in the terminal. Note chromium is what is installed on your system.
* Using bash tool you can start GUI applications, but you need to set export DISPLAY=:1 and use a subshell. For example "(DISPLAY=:1 xterm &)". GUI apps run with bash tool will appear within your desktop environment, but they may take some time to appear. Take a screenshot to confirm it did.
* When using your bash tool with commands that are expected to output very large quantities of text, redirect into a tmp file and use str_replace_editor or `grep -n -B <lines before> -A <lines after> <query> <filename>` to confirm output.
* When viewing a page it can be helpful to zoom out so that you can see everything on the page.  Either that, or make sure you scroll down to see everything before deciding something isn't available.
* When using your computer function calls, they take a while to run and send back to you.  Where possible/feasible, try to chain multiple of these calls all into one function calls request.
* The current date is {datetime.today().strftime('%A, %B %-d, %Y')}.
</SYSTEM_CAPABILITY>

<IMPORTANT>
* When using Chromium, if a startup wizard appears, IGNORE IT.  Do not even click "skip this step".  Instead, click on the address bar where it says "Search or enter address", and enter the appropriate search term or URL there.
* If the item you are looking at is a pdf, if after taking a single screenshot of the pdf it seems that you want to read the entire document instead of trying to continue to read the pdf from your screenshots + navigation, determine the URL, use curl to download the pdf, install and use pdftotext to convert it to a text file, and then read that text file directly with your StrReplaceEditTool.
* If you are at the beginning of the conversation and take a screenshot, the screen may show up black. In this case just move the mouse to the center of the screen and do a left click. Then screenshot again.
</IMPORTANT>

You are a sales research assistant using a Linux virtual desktop. Your task is to:
1. Research companies using Chromium to find:
   - Company overview and size
   - Recent news and developments
   - Technologies used
   - Key decision makers
   - Pain points and opportunities
2. Create detailed research notes in LibreOffice Writer
3. Build a structured spreadsheet in LibreOffice Calc for sales metrics
4. Generate draft outreach messaging
5. Save all materials in an organized folder structure

Guidelines:
- Launch GUI apps using bash with DISPLAY=:1 
- Take screenshots to verify your actions
- Save files in the Documents/sales_research folder
- Format documents professionally
- Focus on finding actionable sales insights
- Note potential trigger events for outreach
- Look for compelling reasons to engage
"""

class ToolCollection:
    def __init__(self, *tools):
        self.tools = tools
        self.tool_map = {tool.to_params()["name"]: tool for tool in tools}

    def to_params(self) -> list:
        return [tool.to_params() for tool in self.tools]

    async def run(self, *, name: str, tool_input: dict) -> ToolResult:
        tool = self.tool_map.get(name)
        if not tool:
            return None
        try:
            return await tool(**tool_input)
        except Exception as e:
            print(f"Error running tool {name}: {e}")
            return None

def make_tool_result(result: ToolResult, tool_use_id: str) -> BetaToolResultBlockParam:
    tool_result_content = []
    is_error = False
    
    if result.error:
        is_error = True
        tool_result_content = result.error
    else:
        if result.output:
            tool_result_content.append({
                "type": "text",
                "text": result.output,
            })
        if result.base64_image:
            tool_result_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": result.base64_image,
                },
            })
    
    return {
        "type": "tool_result",
        "content": tool_result_content,
        "tool_use_id": tool_use_id,
        "is_error": is_error,
    }

async def analyze_competitor(
    competitor_name: str,
):
    """Perform competitive analysis on a single competitor"""
    
    # Initialize Scrapybara VM with explicit instance type
    s = Scrapybara(api_key=SCRAPYBARA_API_KEY)
    instance = s.start(instance_type="medium")
    print(f"Started Scrapybara instance: {instance.id}")

    try:
        # Start browser with explicit CDP URL handling
        cdp_url = instance.browser.start()
        print(f"Browser started with CDP URL: {cdp_url}")

        # Initialize tools
        tools = ToolCollection(
            ComputerTool(instance),
            BashTool(instance),
            EditTool(instance)
        )

        # Initialize chat with Claude
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        messages = []

        # Initial research command
        research_command = f"""Please help me research {competitor_name} for competitive analysis.
        
        {f'Additional context: {notes}' if notes else ''}
        
        Please:
        1. Research the company thoroughly
        2. Create detailed notes in a well-organized document
        3. Build a sales intelligence spreadsheet
        4. Draft potential outreach messages
        5. Save everything in Documents/competitive_intel/{competitor_name}

        Focus on finding compelling reasons to engage and potential pain points we could address.
        """

        messages.append({
            "role": "user",
            "content": [{"type": "text", "text": research_command}],
        })

        while True:
            # Get Claude's response
            response = client.beta.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                messages=messages,
                system=[{"type": "text", "text": SYSTEM_PROMPT}],
                tools=tools.to_params(),
                betas=["computer-use-2024-10-22"]
            )

            # Process tool usage
            tool_results = []
            for content in response.content:
                if content.type == "text":
                    print(f"\nAssistant: {content.text}")
                elif content.type == "tool_use":
                    print(f"\nTool Use: {content.name}")
                    result = await tools.run(
                        name=content.name,
                        tool_input=content.input
                    )
                    
                    if content.name == "bash" and not result:
                        result = await tools.run(
                            name="computer",
                            tool_input={"action": "screenshot"}
                        )
                    
                    if result:
                        tool_result = make_tool_result(result, content.id)
                        tool_results.append(tool_result)
                        
                        if result.output:
                            print(f"Tool Output: {result.output}")
                        if result.error:
                            print(f"Tool Error: {result.error}")

            # Add assistant's response and tool results to messages
            messages.append({
                "role": "assistant",
                "content": [c.model_dump() for c in response.content]
            })

            if tool_results:
                messages.append({
                    "role": "user",
                    "content": tool_results
                })
            else:
                break

    finally:
        instance.stop()
        print(f"\nAnalysis complete for {competitor_name}! Documents saved in Documents/competitive_intel/{competitor_name}")

async def analyze_market(competitors: List[dict]):
    """Analyze multiple competitors in sequence"""
    today = datetime.today().strftime('%Y-%m-%d')
    
    for competitor in competitors:
        print(f"\nStarting analysis for {competitor['name']}...")
        try:
            await analyze_competitor(
                competitor_name=competitor["name"],
                website=competitor["website"],
                focus_areas=competitor.get("focus_areas"),
                previous_analysis_date=competitor.get("last_analysis")
            )
        except Exception as e:
            print(f"Error analyzing {competitor['name']}: {e}")
            continue

if __name__ == "__main__":
    # Example usage
    companies = [
        {
            "name": "TechCorp Solutions",
            "industry": "Enterprise Software",
            "notes": "Recently raised Series B, expanding engineering team"
        },
        {
            "name": "DataFlow Analytics",
            "industry": "Data Analytics",
            "notes": "Looking to improve their ML pipeline efficiency"
        }
    ]
    
    asyncio.run(analyze_market(companies))