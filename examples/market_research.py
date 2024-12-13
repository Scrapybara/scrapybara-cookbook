import asyncio
import os
from typing import Any, cast
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(".env.example")

from anthropic import Anthropic
from anthropic.types.beta import (
    BetaToolResultBlockParam,
    BetaMessageParam,
)

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
</IMPORTANT>

You are a market research assistant using a Linux virtual desktop. Your task is to:
1. Research a given company/product using Chromium
2. Take organized notes in LibreOffice Writer
3. Create a summary spreadsheet in LibreOffice Calc
4. Save all documents in an organized way

Guidelines:
- Launch GUI apps using bash with DISPLAY=:1 
- Take screenshots to verify your actions
- Save files in the Documents folder
- Format documents professionally
"""

class ToolCollection:
    """A collection of anthropic-defined tools."""
    def __init__(self, *tools):
        self.tools = tools
        self.tool_map = {tool.to_params()["name"]: tool for tool in tools}

    def to_params(self) -> list:
        return [tool.to_params() for tool in self.tools]

    async def run(self, *, name: str, tool_input: dict[str, Any]) -> ToolResult:
        tool = self.tool_map.get(name)
        if not tool:
            return None
        try:
            r = await tool(**tool_input)
            return r
        except Exception as e:
            print(f"Error running tool {name}: {e}")
            return None

def make_tool_result(result, tool_use_id: str) -> BetaToolResultBlockParam:
    """Convert tool result to API format"""
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

async def research_company(company_name: str, industry: str = None, notes: str = None):
    """Perform automated sales research on a company"""
    
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
        research_command = f"""Please help me research {company_name}. Follow these steps:
        1. Launch Firefox and search for the company
        2. Open LibreOffice Writer to take detailed notes
        3. Create a spreadsheet summarizing key metrics
        4. Save all documents in Documents folder
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
                    
                    # Handle empty bash results by taking a screenshot
                    if content.name == "bash" and not result:
                        result = await tools.run(
                            name="computer",
                            tool_input={"action": "screenshot"}
                        )
                        print(f"Took fallback screenshot after empty bash result")
                    
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
                # No more tools used - task complete
                break

    finally:
        instance.stop()
        print(f"\nResearch complete for {company_name}!")

if __name__ == "__main__":
    asyncio.run(research_company("Anthropic"))