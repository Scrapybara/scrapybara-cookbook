import asyncio
from playwright.async_api import async_playwright
from anthropic import Anthropic
from scrapybara import Scrapybara
from dotenv import load_dotenv
import os


async def main():
    # Load environment variables
    load_dotenv()

    # Initialize clients
    scrapybara = Scrapybara(api_key=os.getenv("SCRAPYBARA_API_KEY"))
    anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    print("Starting Scrapybara instance...")
    instance = scrapybara.start_ubuntu()

    try:
        # Start browser and get CDP URL
        print("Starting browser...")
        cdp_url = instance.browser.start().cdp_url

        # Load authentication state
        instance.browser.authenticate(auth_state_id=os.getenv("AUTH_STATE_ID"))

        # Connect with Playwright
        async with async_playwright() as playwright:
            browser = await playwright.chromium.connect_over_cdp(cdp_url)
            page = await browser.new_page()

            # Navigate to LinkedIn jobs
            print("Navigating to LinkedIn jobs...")
            await page.goto(
                "https://www.linkedin.com/jobs/search/?keywords=software%20engineer"
            )
            await page.wait_for_timeout(5000)  # Wait 5 seconds

            # Get page content
            content = await page.content()

            # Close browser connection
            await browser.close()

        # Prepare prompt for Claude
        prompt = f"""Analyze this job posting from LinkedIn and create a professional resume in LaTeX format that's tailored to the position. 
        Focus on relevant technical skills and experience that match the job requirements.
        The resume should be well-structured with clear sections for:
        - Contact Information
        - Professional Summary
        - Technical Skills
        - Work Experience
        - Education
        Make it ATS-friendly and emphasize matching qualifications.
        Include proper LaTeX headers and document structure.
        
        Here's the job posting content:
        {content}
        
        Please provide the resume in LaTeX format. Return the LaTeX content only. No other text."""

        # Get resume from Claude
        print("Generating resume with Claude...")
        response = anthropic.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}],
        )

        # Extract LaTeX content
        message = response.content[0].text
        latex_start = message.find("```latex")
        latex_end = message.rfind("```")
        if latex_start != -1 and latex_end != -1:
            latex_content = message[latex_start + 8 : latex_end].strip()
        else:
            latex_content = message  # Fallback if no latex code block found

        # Save LaTeX
        with open("tailored_resume.tex", "w") as f:
            f.write(latex_content)
        print("Resume saved as LaTeX")

    finally:
        # Cleanup
        instance.stop()
        print("Instance stopped")


if __name__ == "__main__":
    asyncio.run(main())
