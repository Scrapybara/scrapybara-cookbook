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
* You are utilizing an Ubuntu virtual machine with Chromium browser installed
* You can navigate repositories and analyze code
* You can take screenshots of interesting findings
* The current date is {datetime.today().strftime('%A, %B %-d, %Y')}
</SYSTEM_CAPABILITY>

You are a GitHub research assistant. Your task is to:
1. Analyze GitHub repositories and profiles
2. Document key findings and insights
3. Evaluate code quality and patterns
4. Track repository activity and contributions
5. Assess documentation quality
6. Create summary reports

Guidelines:
- Focus on meaningful metrics and patterns
- Document interesting findings with screenshots
- Save analysis results in Documents/github_research/
- Organize findings by repository/user
- Consider both quantitative and qualitative aspects

<IMPORTANT>
* When using Chromium, if a startup wizard appears, IGNORE IT. Click directly on the address bar.
* Always wait for pages to fully load before analysis
* Take screenshots of significant findings
* Save your analysis in organized documents
</IMPORTANT>
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

async def analyze_github_profile(github_username: str, context_id: str, description: str = None):
    """Analyze a GitHub profile and its repositories"""
    
    # Initialize Scrapybara VM with explicit instance type
    s = Scrapybara(api_key=SCRAPYBARA_API_KEY)
    instance = s.start(instance_type="medium")
    print(f"Started Scrapybara instance: {instance.id}")

    try:
        # Start browser with explicit CDP URL handling
        cdp_url = instance.browser.start()
        print(f"Browser started with CDP URL: {cdp_url}")
        
        # Authenticate browser with context ID
        instance.browser.authenticate(context_id=context_id)

        # Initialize tools
        tools = ToolCollection(
            ComputerTool(instance),
            BashTool(instance),
            EditTool(instance)
        )

        # Initialize chat with Claude
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        messages = []

        # Initial analysis command
        analysis_command = f"""Please analyze the GitHub profile for: {github_username}
        
        {f'Focus areas: {description}' if description else ''}
        
        Please:
        1. Navigate to github.com/{github_username}
        2. Analyze their profile and repositories:
           - Repository overview and statistics
           - Technology stack and dependencies
           - Contribution patterns and activity
           - Documentation quality
           - Notable projects and achievements
        3. Take screenshots of significant findings
        4. Create a summary document in Documents/github_research/{github_username}/
        
        Provide a comprehensive analysis of their GitHub presence.
        """

        messages.append({
            "role": "user",
            "content": [{"type": "text", "text": analysis_command}],
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

    finally:
        instance.stop()
        print(f"\nAnalysis complete for {github_username}!")

async def run_example_analyses():
    """Run example GitHub profile analyses"""
    analyses = [
        {
            "username": "anthropics",
            "description": "Focus on AI research repositories and documentation",
            "context_id": "anthropics-analysis"
        },
        {
            "username": "openai",
            "description": "Analyze main project repositories and community engagement",
            "context_id": "openai-analysis"
        }
    ]
    
    for analysis in analyses:
        print(f"\nStarting analysis of {analysis['username']}...")
        await analyze_github_profile(
            github_username=analysis["username"],
            description=analysis["description"],
            context_id=analysis["context_id"]
        )

if __name__ == "__main__":
    asyncio.run(run_example_analyses())
