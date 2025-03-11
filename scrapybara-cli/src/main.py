from typing import List
import typer
import os
from scrapybara import Scrapybara
from scrapybara.anthropic import Anthropic
from scrapybara.types import Message, UserMessage, TextPart
from dotenv import load_dotenv
from rich.console import Console
from rich import print
from getpass import getpass
from .agent import run_agent

load_dotenv()

console = Console()
app = typer.Typer()

@app.command()
def main(
    instance_type: str = typer.Option(
        "ubuntu",
        help="Type of instance to start. Must be one of: 'ubuntu', 'browser'",
    ),
    model: str = typer.Option(
        "claude-3-7-sonnet-20250219",
        help="Model to use. Must be one of: 'claude-3-7-sonnet-20250219', 'claude-3-5-sonnet-20241022'",
    )
):
    """
    Run the CLI-based computer agent, powered by Scrapybara and Anthropic!
    """
    # Check for required environment variables
    scrapybara_key = os.getenv("SCRAPYBARA_API_KEY")

    if not scrapybara_key:
        scrapybara_key = getpass("Please enter your Scrapybara API key: ").strip()
        os.environ["SCRAPYBARA_API_KEY"] = scrapybara_key
        if not scrapybara_key:
            raise typer.BadParameter("Scrapybara API key is required to continue.")

    if instance_type not in ["ubuntu", "browser"]:
        raise typer.BadParameter(
            'instance_type must be one of: "ubuntu", "browser"'
        )
    
    if model not in ["claude-3-7-sonnet-20250219", "claude-3-5-sonnet-20241022"]:
        raise typer.BadParameter(
            'model must be one of: "claude-3-7-sonnet-20250219", "claude-3-5-sonnet-20241022"'
        )

    # Initialize Scrapybara with the API key
    scrapybara = Scrapybara(api_key=scrapybara_key)
    run_conversation(instance_type, scrapybara, model)


def run_conversation(instance_type: str, scrapybara: Scrapybara, model_name: str):
    instance = None
    try:
        with console.status("[bold green]Starting instance...[/bold green]") as status:
            instance = scrapybara.start_ubuntu() if instance_type == "ubuntu" else scrapybara.start_browser()
            status.update("[bold green]Instance started![/bold green]")

        print(f"[bold blue]Stream URL: {instance.get_stream_url().stream_url}[/bold blue]")
        print("[bold yellow]Press Ctrl+C to stop the instance at any time[/bold yellow]")
        
        model = Anthropic(name=model_name)
        messages: List[Message] = []

        while True:
            prompt = input("> ")
            messages.append(UserMessage(content=[TextPart(text=prompt)]))
            messages = run_agent(scrapybara, model, instance, messages)
    except Exception as e:
        if e not in [KeyboardInterrupt, EOFError]:
            print(f"[bold red]Error: {e}[/bold red]")
    finally:
        if instance:
            with console.status("[bold red]Stopping instance...[/bold red]") as status:
                instance.stop()
                status.update("[bold red]Instance stopped![/bold red]")


if __name__ == "__main__":
    app()
