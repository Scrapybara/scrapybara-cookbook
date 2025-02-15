import asyncio
import base64
from datetime import datetime
from typing import Any, cast
from anthropic import Anthropic
from playwright.async_api import async_playwright
from scrapybara import Scrapybara
from scrapybara.anthropic import BashTool, ComputerTool, EditTool, ToolResult
from dotenv import load_dotenv
import os

SYSTEM_PROMPT = """
<SYSTEM_CAPABILITY>
* You have access to an Ubuntu virtual machine with internet connectivity
* You can install Ubuntu applications using the bash tool (use curl over wget)
* To run GUI applications with the bash tool:
  - Use a subshell, e.g. "(DISPLAY=:1 xterm &)"
  - GUI apps will appear but may take time to load - confirm with an extra screenshot
* Start Chromium (default browser) via the bash tool "(DISPLAY=:1 chromium &)", but interact with it visually via the computer tool
* Start LibreOffice (default word processor) via the bash tool "(DISPLAY=:1 libreoffice --writer &)", but interact with it visually via the computer tool
* In Chromium, click the address bar directly to enter URLs/searches
* If you need to read a full PDF after initial screenshot
  - Download with curl
  - Convert to text using pdftotext
  - Read the text file with StrReplaceEditTool
* If you need to read a HTML file:
  - Open with the address bar in Chromium
* For commands with large text output:
  - Redirect to a temp file
  - Use str_replace_editor or grep with context (-B and -A flags) to view output
* When viewing pages:
  - Zoom out to see full content, or
  - Scroll to ensure you see everything
* Computer function calls take time, string together calls when possible
* You are allowed to take actions on behalf of the user on sites that are authenticated
* To login additional sites, ask the user to use Auth Contexts or the Interactive Desktop
* Today's date is {datetime.today().strftime('%A, %B %-d, %Y')}
</SYSTEM_CAPABILITY>

<IMPORTANT>
* If first screenshot shows black screen:
  - Click mouse in screen center
  - Take another screenshot
* When interacting with a field, always clear the field first using "ctrl+A" and "delete"
  - Take an extra screenshot after clicking "enter" to confirm the field is properly submitted and move the mouse to the next field
* When typing text in a word document, explicitly type "enter" to create a new line
  - Stop between each paragraph and new line to type enter, the newline symbol does not get registered
* Research facts with Google searches in Chromium, read results thoroughly
* Use more generalized websites during research, e.g. use Google Flights instead of United when searching for flights, only use United when finalizing bookings
* Wait for actions to complete (examine previous screenshots) before taking another action
* You have to execute the command without additional input from the user
* Look at the screen using a screenshot, you should be situated in a browser or an application, follow the user's command!
</IMPORTANT>

You are a web developer tasked with replicating websites.
Your approach should be:
1. Analyze the provided website content and screenshot
2. Create a single index.html file that mimics the layout and styling
3. Use internal CSS and vanilla JavaScript only - no external dependencies
4. Focus on visual similarity, not functionality
5. Compare your result with the original screenshot and improve
6. Use original image sources found in the HTML, do not make up new ones
"""


class WebsiteCopycat:
    def __init__(self, scrapybara_api_key: str, anthropic_api_key: str):
        self.scrapybara = Scrapybara(api_key=scrapybara_api_key, timeout=600)
        self.anthropic = Anthropic(api_key=anthropic_api_key)
        self.instance = None
        self.browser = None
        self.page = None

    async def start(self):
        """Start Scrapybara instance and browser"""
        print("Starting Scrapybara instance...")
        self.instance = self.scrapybara.start_ubuntu()
        print("Instance started: ", self.instance.id)

        # Start browser session
        cdp_url = self.instance.browser.start().cdp_url
        print("CDP URL: ", cdp_url)

        # Connect with Playwright async
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.connect_over_cdp(cdp_url)
        self.page = await self.browser.new_page()
        print("Page created: ", await self.page.title())

    async def capture_website(self, url: str) -> tuple[str, str]:
        """Capture website content and screenshot"""
        print(f"Capturing website: {url}")
        await self.page.goto(url)

        # Wait and scroll for dynamic content
        await self.page.wait_for_timeout(3000)
        await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await self.page.wait_for_timeout(2000)

        # Get content and screenshot
        content = await self.page.content()
        await self.page.evaluate("window.scrollTo(0, 0)")
        screenshot = await self.page.screenshot(
            path="/tmp/original.png", full_page=True
        )

        return content, base64.b64encode(screenshot).decode()

    def create_system_prompt(self, html_content: str):
        return (
            SYSTEM_PROMPT
            + f"""
    
I'll show you a website's HTML content and screenshot. Create a single index.html file that replicates this website's appearance.

Here's the original website content:
{html_content[:50000]}... (truncated)

Let's start by creating index.html and adding the initial HTML structure.
Once you've created the file, open it in Chrome to check how it looks.
Everytime you make a change, inspect the result by reloading it in the browser and taking a screenshot.
Do not exit the loop or stop making tool calls until you've opened the file in Chrome and visually inspected it using screenshot at least once.
Once you've inspected the file, compare it with the original screenshot and improve if needed, or provide your final reasoning in text about why it's satisfactory."""
        )

    async def replicate_website(self, html_content: str, screenshot: str):
        """Use Claude to create a replica of the website"""
        print("Starting website replication...")

        tool_collection = ToolCollection(
            ComputerTool(self.instance),
            BashTool(self.instance),
            EditTool(self.instance),
        )

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""Here's a screenshot of the website you're trying to replicate:""",
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": screenshot,
                        },
                    },
                ],
            }
        ]

        while True:
            response = self.anthropic.beta.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=8192,
                messages=messages,
                system=[
                    {"type": "text", "text": self.create_system_prompt(html_content)}
                ],
                tools=tool_collection.to_params(),
                betas=["computer-use-2024-10-22"],
            )

            response_params = [block.model_dump() for block in response.content]
            tool_result_content = []

            # Process each content block in the response
            for block in response_params:
                if block["type"] == "text":
                    print(f"\nClaude: {block['text']}")
                elif block["type"] == "tool_use":
                    print(f"\nUsing tool: {block['name']}")
                    print(f"Tool input: {block['input']}")

                    result = await tool_collection.run(
                        name=block["name"], tool_input=block["input"]
                    )
                    print(f"Tool result: {result}")

                    # For bash commands with empty results, take a screenshot
                    if block["name"] == "bash" and (
                        not result
                        or (
                            result.output == ""
                            and result.error == ""
                            and result.base64_image is None
                        )
                    ):
                        result = await tool_collection.run(
                            name="computer", tool_input={"action": "screenshot"}
                        )

                    if result:
                        tool_result = {
                            "type": "tool_result",
                            "tool_use_id": block["id"],
                            "content": (
                                [{"type": "text", "text": result.output}]
                                if result.output
                                else []
                            ),
                            "is_error": bool(result.error),
                        }

                        if result.base64_image:
                            tool_result["content"].append(
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/png",
                                        "data": result.base64_image,
                                    },
                                }
                            )

                        tool_result_content.append(tool_result)

            # Update chat history
            messages.append({"role": "assistant", "content": response_params})

            if tool_result_content:
                messages.append({"role": "user", "content": tool_result_content})
            else:
                # If no tool results and Claude indicates completion, break
                break

    async def cleanup(self):
        """Clean up resources"""
        if self.browser:
            await self.browser.close()
        if self.instance:
            self.instance.stop()


class ToolCollection:
    """Tool collection for Claude"""

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
            return await tool(**tool_input)
        except Exception as e:
            print(f"Error running tool {name}: {e}")
            return None


async def main():
    # Load environment variables from .env file
    load_dotenv(override=True)

    copycat = WebsiteCopycat(
        scrapybara_api_key=os.getenv("SCRAPYBARA_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

    try:
        await copycat.start()
        print("Scrapybara instance started")
        content, screenshot = await copycat.capture_website("https://ycombinator.com")
        print("Website captured")
        await copycat.replicate_website(content, screenshot)
    finally:
        await copycat.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
