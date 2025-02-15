import asyncio
from datetime import datetime
from typing import Any, cast
from anthropic import Anthropic
from scrapybara import Scrapybara
from scrapybara.anthropic import BashTool, ComputerTool, EditTool, ToolResult
from dotenv import load_dotenv
import os

SYSTEM_PROMPT = f"""<SYSTEM_CAPABILITY>
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

You are an AI playing Dungeon Crawl Stone Soup (DCSS), a roguelike RPG.
Your goal is to explore the dungeon, fight monsters, and survive.

DO NOT STOP AND ASK THE USER FOR ANYTHING. JUST KEEP PLAYING THE GAME.

Key information:
- The game is turn-based, so take your time to think
- You can see your health, mana, and status in the interface
- Use keyboard commands for movement (yuhjklbn) and actions
- '?' shows help, 'i' for inventory, 'g' to pick up items
- Read the messages at the bottom of the screen carefully
- To exit the loop/game, type "quit" or "exit" in a text message response"""


class GameAgent:
    def __init__(self, scrapybara_api_key: str, anthropic_api_key: str):
        self.scrapybara = Scrapybara(api_key=scrapybara_api_key, timeout=600)
        self.anthropic = Anthropic(api_key=anthropic_api_key)
        self.instance = None

    def start(self):
        """Start Scrapybara instance and install game"""
        print("Starting Scrapybara instance...")
        self.instance = self.scrapybara.start_ubuntu()

        # Install DCSS using bash
        install_cmd = "sudo apt-get install -y crawl-tiles"
        self.instance.bash(command=install_cmd)

    async def play_game(self):
        """Start the game and let Claude play"""
        print("Starting game session...")

        # Start the game
        self.instance.bash(command="(DISPLAY=:1 /usr/games/crawl-tiles &)")

        # Setup tools for Claude
        tool_collection = ToolCollection(
            ComputerTool(self.instance),
            BashTool(self.instance),
            EditTool(self.instance),
        )

        initial_prompt = """I've started Dungeon Crawl Stone Soup for you. 
Let's create a character and start playing! 

1. First, take a look at the game screen
2. We'll create a beginner-friendly character
3. Then you can start exploring the dungeon"""

        messages = [
            {"role": "user", "content": [{"type": "text", "text": initial_prompt}]}
        ]

        while True:
            response = self.anthropic.beta.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                messages=messages,
                system=[{"type": "text", "text": SYSTEM_PROMPT}],
                tools=tool_collection.to_params(),
                betas=["computer-use-2024-10-22"],
            )

            response_params = [block.model_dump() for block in response.content]
            tool_result_content = []

            # Check if response contains text that's not an exit command
            has_non_exit_text = any(
                block["type"] == "text"
                and not (
                    "exit" in block["text"].lower() or "quit" in block["text"].lower()
                )
                for block in response_params
            )

            # Process each content block in the response
            for block in response_params:
                if block["type"] == "text":
                    print(f"\nClaude: {block['text']}")
                elif block["type"] == "tool_use":
                    print(f"\nUsing tool: {block['name']}")

                    result = await tool_collection.run(
                        name=block["name"], tool_input=block["input"]
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
            elif has_non_exit_text:
                # Add the "keep playing" message if there was non-exit text
                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "just keep playing the game and don't ask questions. if you want to exit, type 'exit' or 'quit' in a text message response",
                            }
                        ],
                    }
                )

            # Check for game over or user interruption
            if any(
                "exit" in block["text"].lower() or "quit" in block["text"].lower()
                for block in response_params
                if block["type"] == "text"
            ):
                break

    def cleanup(self):
        """Clean up resources"""
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

    load_dotenv(override=True)

    agent = GameAgent(
        scrapybara_api_key=os.getenv("SCRAPYBARA_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

    try:
        agent.start()
        await agent.play_game()
    finally:
        agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
