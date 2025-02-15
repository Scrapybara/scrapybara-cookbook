from .prompt import SYSTEM_PROMPT
from .helpers import ToolCollection, make_tool_result
from scrapybara.client import BaseInstance
from anthropic import Anthropic
from rich import print


async def run_agent(instance: BaseInstance, tools: ToolCollection, prompt: str) -> None:
    anthropic = Anthropic()

    stream_url = instance.get_stream_url().stream_url

    messages = []
    messages.append({"role": "user", "content": [{"type": "text", "text": prompt}]})

    while True:
        # Get Claude's response
        response = anthropic.beta.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            messages=messages,
            system=[{"type": "text", "text": SYSTEM_PROMPT}],
            tools=tools.to_params(),
            betas=["computer-use-2024-10-22"],
        )

        # Process tool usage
        tool_results = []
        for content in response.content:
            if content.type == "text":
                print(f"\n{content.text}")
            elif content.type == "tool_use":
                text = f"Running {content.name} with {content.input}"

                if content.name == "computer":
                    if content.input["action"] == "screenshot":  # type: ignore
                        text = "[bold yellow]Taking screenshot[/bold yellow]"
                    elif content.input["action"] == "left_click" or content.input["action"] == "right_click":  # type: ignore
                        text = "[bold yellow]Clicking[/bold yellow]"
                    elif content.input["action"] == "type":  # type: ignore
                        text = "[bold yellow]Typing[/bold yellow]"
                    elif content.input["action"] == "scroll":  # type: ignore
                        text = "[bold yellow]Scrolling[/bold yellow]"
                    elif content.input["action"] == "key":  # type: ignore
                        text = f"[bold yellow]Pressing key '{content.input['text'].upper()}'[/bold yellow]"  # type: ignore
                    elif content.input["action"] == "mouse_move":  # type: ignore
                        text = "[bold yellow]Moving mouse[/bold yellow]"

                if content.name == "bash":
                    text = f"[green]scrapybara[/green]@[white]{stream_url.replace('http://', '').split(':')[0]}[/white]# {content.input['command']}"  # type: ignore

                print(f"{text}")

                result = await tools.run(
                    name=content.name, tool_input=content.input  # type: ignore
                )

                tool_result = make_tool_result(result, content.id)
                tool_results.append(tool_result)

                if result.output:
                    print(f"[green]{result.output}[/green]")
                if result.error:
                    print(f"[red]{result.error}[/red]")

        # Add assistant's response and tool results to messages
        messages.append(
            {"role": "assistant", "content": [c.model_dump() for c in response.content]}
        )

        if tool_results:
            messages.append({"role": "user", "content": tool_results})
        else:
            break
