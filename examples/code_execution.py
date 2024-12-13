import asyncio
import os
from typing import Any, Dict
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
* You are utilising an Ubuntu virtual machine with Python and common data science libraries installed.
* You can execute Python code directly in the environment using the code_execution tool.
* Available packages include numpy, pandas, matplotlib, scikit-learn, and other common data science libraries.
* You can also use bash commands and control the virtual desktop if needed.
* To open chromium, use: "(DISPLAY=:1 chromium --no-sandbox &)" in the terminal
* The current date is {datetime.today().strftime('%A, %B %-d, %Y')}.
</SYSTEM_CAPABILITY>

You are a Python coding assistant. Your task is to:
1. Help users write and test Python code
2. Demonstrate coding concepts with examples
3. Debug and optimize code
4. Create data visualizations
5. Perform data analysis tasks
6. Save code and results in organized files

Guidelines:
- Break down complex problems into smaller steps
- Include error handling in your code
- Use visualizations when helpful
- Explain your code and results clearly
- Save important code in Documents/code_examples
"""

class CodeExecutionTool:
    """Tool for executing Python code in a Scrapybara instance."""
    
    def __init__(self, instance):
        self.instance = instance

    def to_params(self) -> Dict[str, Any]:
        return {
            "name": "code_execution",
            "description": """Execute Python code in the virtual environment. 
            The code will be executed in a fresh Python kernel each time.
            Available packages include numpy, pandas, matplotlib, and other common libraries.
            
            Input should be a dictionary with:
            - code: The Python code to execute (required)
            - timeout: Maximum execution time in seconds (optional, default 30)""",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to execute"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Maximum execution time in seconds",
                        "default": 30
                    }
                },
                "required": ["code"]
            }
        }

    async def __call__(self, code: str, timeout: int = 30) -> ToolResult:
        try:
            response = await self.instance.code.execute(
                code=code,
                timeout=timeout,
                kernel_name="python3"
            )
            
            # Extract output from the response format
            output = ""
            if isinstance(response, dict):  # Handle both dict and direct output formats
                for output_item in response.get("outputs", []):
                    if output_item.get("type") == "stream" and output_item.get("name") == "stdout":
                        output += output_item.get("text", "")
            else:
                output = str(response)
            
            return ToolResult(
                output=output,
                error=response.get("error") if isinstance(response, dict) else None,
                base64_image=None
            )
        except Exception as e:
            return ToolResult(error=str(e))

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

async def coding_session(task: str, description: str = None, save_output: bool = True):
    """Start a coding assistance session for a specific task"""
    
    # Initialize Scrapybara VM
    s = Scrapybara(api_key=SCRAPYBARA_API_KEY)
    instance = s.start(instance_type="medium")
    print(f"Started Scrapybara instance: {instance.id}")

    # Initialize tools
    tools = ToolCollection(
        CodeExecutionTool(instance),
        BashTool(instance),
        ComputerTool(instance),
        EditTool(instance)
    )

    # Initialize chat with Claude
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    messages = []

    # Initial coding task
    coding_command = f"""Please help me with the following coding task: {task}
    
    {f'Additional context: {description}' if description else ''}
    
    Please:
    1. Break down the problem into steps
    2. Write and test the code
    3. Include error handling
    4. Add helpful comments
    5. Save the final code in Documents/code_examples/
    
    Focus on writing clean, efficient, and well-documented code.
    """

    messages.append({
        "role": "user",
        "content": [{"type": "text", "text": coding_command}],
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
                print(f"\nExecuting: {content.name}")
                result = await tools.run(
                    name=content.name,
                    tool_input=content.input
                )
                
                if result:
                    tool_result = make_tool_result(result, content.id)
                    tool_results.append(tool_result)
                    
                    if result.output:
                        print(f"Output: {result.output}")
                    if result.error:
                        print(f"Error: {result.error}")

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

    instance.stop()
    print(f"\nCoding session complete! Code saved in Documents/code_examples/")

async def run_example_tasks():
    """Run a series of example coding tasks"""
    tasks = [
        {
            "task": "Create a data visualization example",
            "description": "Generate a sample dataset and create multiple types of plots using matplotlib"
        },
        {
            "task": "Implement and benchmark sorting algorithms",
            "description": "Implement bubble sort and quicksort, then compare their performance"
        },
        {
            "task": "Analyze a dataset with pandas",
            "description": "Load sample data, perform common DataFrame operations, and create summary statistics"
        }
    ]
    
    for task in tasks:
        print(f"\nStarting task: {task['task']}...")
        await coding_session(
            task=task["task"],
            description=task["description"]
        )

if __name__ == "__main__":
    asyncio.run(run_example_tasks())
