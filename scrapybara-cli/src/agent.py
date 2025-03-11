from typing import List, Dict, Any
from scrapybara import Scrapybara
from scrapybara.client import BaseInstance, BrowserInstance
from scrapybara.types import Tool, Model, Message
from scrapybara.anthropic import BROWSER_SYSTEM_PROMPT, UBUNTU_SYSTEM_PROMPT
from scrapybara.tools import ComputerTool, BashTool, EditTool
from rich import print

def format_computer_action(action: str, args: Dict[str, Any]) -> str:
    if args:
        if action == "move_mouse":
            return f"[bold yellow]Moving mouse to ({args['coordinates'][0]}, {args['coordinates'][1]})[/bold yellow]"
        elif action == "click_mouse":
            pos = f" at ({args['coordinates'][0]}, {args['coordinates'][1]})" if args.get('coordinates') else ""
            click_desc = f"{args.get('num_clicks', 1)}x " if args.get('num_clicks', 1) > 1 else ""
            return f"[bold yellow]{click_desc}{args['button'].title()} {args.get('click_type', 'click')}{pos}[/bold yellow]"
        elif action == "drag_mouse":
            start = args['path'][0]
            end = args['path'][-1]
            return f"[bold yellow]Dragging mouse from ({start[0]}, {start[1]}) to ({end[0]}, {end[1]})[/bold yellow]"
        elif action == "scroll":
            pos = f" at ({args['coordinates'][0]}, {args['coordinates'][1]})" if args.get('coordinates') else ""
            scroll_desc = []
            if args.get('delta_x'):
                scroll_desc.append(f"horizontally by {args['delta_x']}")
            if args.get('delta_y'):
                scroll_desc.append(f"vertically by {args['delta_y']}")
            return f"[bold yellow]Scrolling {' and '.join(scroll_desc)}{pos}[/bold yellow]"
        elif action == "press_key":
            keys = '+'.join(args['keys'])
            duration = f" for {args['duration']}s" if args.get('duration') else ""
            return f"[bold yellow]Pressing {keys}{duration}[/bold yellow]"
        elif action == "type_text":
            return f"[bold yellow]Typing: {args['text']}[/bold yellow]"
        elif action == "wait":
            return f"[bold yellow]Waiting for {args['duration']}s[/bold yellow]"
        elif action == "take_screenshot":
            return "[bold yellow]Taking screenshot[/bold yellow]"
        elif action == "get_cursor_position":
            return "[bold yellow]Getting cursor position[/bold yellow]"
        return f"[bold yellow]{action}: {args}[/bold yellow]"
    return f"[bold yellow]{action}: unknown args[/bold yellow]"

def handle_step(step):
    print(step.text)
    if step.tool_calls:
        for call in step.tool_calls:
            if call.tool_name == "computer":
                print(format_computer_action(call.args["action"], call.args))
            elif call.tool_name == "bash":
                print(f"[green]$[/green] {call.args['command']}")
            else:
                print(f"[green]{call.tool_name}[/green] → {', '.join(f'{k}={v}' for k,v in call.args.items())}")

def run_agent(client: Scrapybara, model: Model, instance: BaseInstance, messages: List[Message]) -> List[Message]:
    # Determine which system prompt to use based on the instance type
    if isinstance(instance, BrowserInstance):
        system = BROWSER_SYSTEM_PROMPT
        tools: List[Tool] = [ComputerTool(instance)]
    else:
        system = UBUNTU_SYSTEM_PROMPT
        tools: List[Tool] = [ComputerTool(instance), BashTool(instance), EditTool(instance)]

    try:
        response = client.act(
            model=model,
            tools=tools,
            system=system,
            messages=messages,
            on_step=handle_step,
        )
        return response.messages
    except Exception as e:
        print(f"[red]Error: {str(e)}[/red]")
        return messages
