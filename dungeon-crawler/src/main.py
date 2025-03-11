from typing import Optional
from scrapybara import Scrapybara
from scrapybara.anthropic import Anthropic, UBUNTU_SYSTEM_PROMPT
from scrapybara.tools import ComputerTool
from scrapybara.types import Model
from dotenv import load_dotenv
import os

TASK_PROMPT = """<TASK>
You are an expert gamer playing Dungeon Crawl Stone Soup (DCSS), a roguelike RPG.
Your goal is to explore the dungeon, fight monsters, and survive.

- The game is turn-based, so take your time to think
- You can see your health, mana, and status in the interface
- Use keyboard commands for movement (yuhjklbn) and actions
- '?' shows help, 'i' for inventory, 'g' to pick up items
- Read the messages at the bottom of the screen carefully

DO NOT STOP AND ASK THE USER FOR ANYTHING. JUST KEEP PLAYING THE GAME.
</TASK>"""

class DungeonCrawler:
    def __init__(self, model: Model, scrapybara_api_key: Optional[str] = None):
        load_dotenv()
        self.model = model
        self.client = Scrapybara(api_key=scrapybara_api_key or os.getenv("SCRAPYBARA_API_KEY"))
        self.instance = None

    def initialize(self):
        self.instance = self.client.start_ubuntu()
        print("₍ᐢ•(ܫ)•ᐢ₎ Started Ubuntu instance: ", self.instance.get_stream_url().stream_url)

        # Install DCSS using bash
        install_cmd = "sudo apt-get install -y crawl-tiles"
        self.instance.bash(command=install_cmd)
        print("₍ᐢ•(ܫ)•ᐢ₎ Installed DCSS")

        # Start the game
        self.instance.bash(command="(DISPLAY=:1 /usr/games/crawl-tiles &)")
        print("₍ᐢ•(ܫ)•ᐢ₎ Started game")

    def handle_step(self, step):
        print(f"₍ᐢ•(ܫ)•ᐢ₎: {step.text}")
        if step.tool_calls:
            for call in step.tool_calls:
                print(f"{call.tool_name} → {', '.join(f'{k}={v}' for k,v in call.args.items())}")

    def play_game(self):
        print("Starting gameplay...")

        INITIAL_PROMPT = """I've started Dungeon Crawl Stone Soup for you. 
Create a cool character with a unique name and start exploring the dungeon! """

        self.client.act(
            model=self.model,
            tools=[ComputerTool(self.instance)],
            system=f"{UBUNTU_SYSTEM_PROMPT}\n\n{TASK_PROMPT}",
            prompt=INITIAL_PROMPT,
            on_step=self.handle_step
        )

    def cleanup(self):
        if self.instance:
            self.instance.stop()


def main():
    # Example usage
    model = Anthropic()
    agent = DungeonCrawler(
        model=model,
    )

    try:
        agent.initialize()
        agent.play_game()
    except Exception as e:
        print(f"₍ᐢ•(ܫ)•ᐢ₎ Error: {e}")
    finally:
        agent.cleanup()


if __name__ == "__main__":
    main()
