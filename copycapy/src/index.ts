import { ScrapybaraClient, Scrapybara, UbuntuInstance } from "scrapybara";
import { anthropic, UBUNTU_SYSTEM_PROMPT } from "scrapybara/anthropic";
// import { openai, UBUNTU_SYSTEM_PROMPT } from "scrapybara/openai";
import { editTool, bashTool, computerTool } from "scrapybara/tools";
import * as dotenv from "dotenv";
import { chromium, Page, Browser } from "playwright";
import chalk from "chalk";

interface PageData {
  url: string;
  html: string;
  css: string[];
}

class CopyCapy {
  private model: Scrapybara.Model;
  private client: ScrapybaraClient;
  private instance: UbuntuInstance | null = null;
  private browser: Browser | null = null;

  constructor(model: Scrapybara.Model, apiKey?: string) {
    dotenv.config();
    this.model = model;
    this.client = new ScrapybaraClient({
      apiKey: apiKey || process.env.SCRAPYBARA_API_KEY,
    });
  }

  private async scrapePageData(page: Page): Promise<PageData> {
    const url = await page.url();
    console.log(
      chalk.blue("₍ᐢ•(ܫ)•ᐢ₎ Scraping ") + chalk.underline(url) + "..."
    );

    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(2000);

    // Scroll to bottom for dynamic content
    await Promise.race([
      page.evaluate(() => {
        window.scrollTo(0, document.body.scrollHeight);
      }),
      new Promise((resolve) => setTimeout(resolve, 2000)),
    ]);
    await page.waitForTimeout(2000);

    // Get CSS URLs and content
    const cssUrls = await page.evaluate(() => {
      const urls = new Set<string>();
      document.querySelectorAll('link[rel="stylesheet"]').forEach((link) => {
        const href = link.getAttribute("href");
        if (href) urls.add(href);
      });
      return Array.from(urls);
    });

    // Download CSS files
    const css = await Promise.all(
      cssUrls.map(async (url) => {
        try {
          return await fetch(url).then((r) => r.text());
        } catch (e) {
          console.error(chalk.red(`₍ᐢ•(ܫ)•ᐢ₎ Failed to fetch CSS from ${url}`));
          return "";
        }
      })
    ).then((results) => results.filter((content) => content.length > 0));

    // Get HTML
    const html = await page.evaluate((pageUrl) => {
      const root = document.documentElement.cloneNode(true) as HTMLElement;
      [
        "script",
        'link[rel="stylesheet"]',
        'link[rel="modulepreload"]',
        'link[rel="preload"]',
      ].forEach((selector) =>
        root.querySelectorAll(selector).forEach((el) => el.remove())
      );

      // Convert all relative image URLs to absolute URLs
      root.querySelectorAll("img").forEach((img) => {
        const src = img.getAttribute("src");
        if (src) {
          try {
            const absoluteUrl = new URL(src, pageUrl).href;
            img.setAttribute("src", absoluteUrl);
          } catch (e) {
            console.warn("Failed to convert URL:", src);
          }
        }
      });

      // Also handle background images in style attributes
      root.querySelectorAll('[style*="background"]').forEach((el) => {
        const style = el.getAttribute("style");
        if (style) {
          const urlMatch = style.match(/url\(['"]?([^'"]+)['"]?\)/);
          if (urlMatch && urlMatch[1]) {
            try {
              const absoluteUrl = new URL(urlMatch[1], pageUrl).href;
              el.setAttribute("style", style.replace(urlMatch[1], absoluteUrl));
            } catch (e) {
              console.warn("Failed to convert background URL:", urlMatch[1]);
            }
          }
        }
      });
      return root.outerHTML;
    }, url);

    return { url, html, css };
  }

  async capyfy(url: string): Promise<void> {
    try {
      // Start Ubuntu instance and browser
      this.instance = await this.client.startUbuntu();
      console.log(
        chalk.green("₍ᐢ•(ܫ)•ᐢ₎ Started Ubuntu instance: "),
        (await this.instance.getStreamUrl()).streamUrl
      );
      const cdpUrl = (await this.instance.browser.start()).cdpUrl;
      this.browser = await chromium.connectOverCDP({ endpointURL: cdpUrl });

      // Scrape the target page
      const page = await this.browser.contexts()[0].pages()[0];
      await page.goto(url, { waitUntil: "networkidle" });
      const pageData = await this.scrapePageData(page);

      // Save HTML with CSS links
      const cssLinks = pageData.css
        .map((_, i) => `<link rel="stylesheet" href="style_${i}.css">`)
        .join("\n    ");
      const html = pageData.html.replace(
        "</head>",
        `    ${cssLinks}\n  </head>`
      );
      await this.instance.file.write({
        path: `copycapy/index.html`,
        content: html,
      });

      // Save CSS files
      await Promise.all(
        pageData.css.map((css, i) =>
          this.instance!.file.write({
            path: `copycapy/style_${i}.css`,
            content: css,
          })
        )
      );

      // Capyfy website
      console.log(chalk.yellow("₍ᐢ•(ܫ)•ᐢ₎ Starting capyfication..."));
      await this.client.act({
        model: this.model,
        tools: [
          computerTool(this.instance),
          bashTool(this.instance),
          editTool(this.instance),
        ],
        system: `${UBUNTU_SYSTEM_PROMPT}
<TASK>
You are an expert web developer. A webscraper has saved the HTML/CSS for ${url} at /home/scrapybara/copycapy.
Your job is to customize the page to make it capybara-themed.
Open the index.html file in Chromium and edit the HTML/CSS to make it capybara-themed.
Make it fun!
</TASK>

<GUIDELINES>
- Interact with Chromium using the computer tool and open pages with the address bar
- Refresh the page after every edit to examine the changes
- Use str_replace_editor instead to view and edit the file
- Avoid grep or other bash tools
</GUIDELINES>`,
        prompt: `Open the page in Chromium and begin customizing ${url}!`,
        onStep: (step) => {
          if (step.text) {
            console.log(chalk.cyan("₍ᐢ•(ܫ)•ᐢ₎:"), step.text);
          }
          if (step.toolCalls?.length) {
            step.toolCalls.forEach((call) => {
              const args = Object.entries(call.args)
                .map(
                  ([key, value]) => `${chalk.dim(key)}=${chalk.yellow(value)}`
                )
                .join(", ");
              console.log(chalk.bold(call.toolName), chalk.dim("→"), args);
            });
          }
        },
      });

      console.log(chalk.green("₍ᐢ•(ܫ)•ᐢ₎ Customization complete! ✨"));
    } catch (error) {
      console.error(chalk.red("₍ᐢ•(ܫ)•ᐢ₎ Error:"), error);
    } finally {
      // Cleanup
      if (this.browser) await this.browser.close();
      if (this.instance) await this.instance.stop();
    }
  }
}

// Example usage
const model = anthropic();
// const model = openai();
const copyCapy = new CopyCapy(model);

await copyCapy.capyfy("https://manus.im");

export default CopyCapy;
