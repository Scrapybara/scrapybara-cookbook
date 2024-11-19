import asyncio
import os
from typing import Any, cast
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from anthropic import Anthropic
from anthropic.types.beta import (
    BetaToolResultBlockParam,
    BetaMessageParam,
)

from scrapybara import Scrapybara
from scrapybara.anthropic import BashTool, ComputerTool, EditTool, ToolResult

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
SCRAPYBARA_API_KEY = os.getenv("SCRAPYBARA_API_KEY")

SYSTEM_PROMPT = """You are a market research assistant using a Linux virtual desktop. Your task is to:
1. Research a given company/product using Firefox
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

async def research_company(company_name: str):
    """Perform market research on a company using AI-driven desktop automation"""
    
    # Initialize Scrapybara VM
    s = Scrapybara(api_key=SCRAPYBARA_API_KEY)
    instance = s.start(instance_type="medium")
    print(f"Started Scrapybara instance: {instance.instance_id}")
    print(f"Instance URL: {s.get_stream_url(instance.instance_id)}")

    # Initialize tools
    tools = ToolCollection(
        ComputerTool(s, instance.instance_id),
        BashTool(s, instance.instance_id),
        EditTool(s, instance.instance_id)
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

    print("\nResearch complete! Documents have been saved.")

if __name__ == "__main__":
    asyncio.run(research_company("Anthropic"))