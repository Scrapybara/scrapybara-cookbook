import {
  type Scrapybara,
  ScrapybaraClient,
  ScrapybaraError,
  type UbuntuInstance,
} from "scrapybara";
import {
  anthropic,
  UBUNTU_SYSTEM_PROMPT as ANTHROPIC_UBUNTU_SYSTEM_PROMPT,
  BROWSER_SYSTEM_PROMPT as ANTHROPIC_BROWSER_SYSTEM_PROMPT,
} from "scrapybara/anthropic";
import {
  openai,
  UBUNTU_SYSTEM_PROMPT as OPENAI_UBUNTU_SYSTEM_PROMPT,
  BROWSER_SYSTEM_PROMPT as OPENAI_BROWSER_SYSTEM_PROMPT,
} from "scrapybara/openai";
import { bashTool, computerTool, editTool } from "scrapybara/tools";

export async function POST(req: Request) {
  const { apiKey, instanceId, instanceType, modelName, messages } =
    (await req.json()) as {
      apiKey: string;
      instanceId: string;
      instanceType: "ubuntu" | "browser";
      modelName: string;
      messages: Scrapybara.Message[];
    };

  // Create a streaming response to send real-time updates back to the client
  const stream = new ReadableStream({
    async start(controller) {
      try {
        const client = new ScrapybaraClient({
          apiKey,
        });

        const instance = await client.get(instanceId);

        const model = modelName.toLowerCase().startsWith("claude")
          ? anthropic({ name: modelName })
          : openai({ name: modelName });

        const tools: Scrapybara.Tool[] =
          instanceType === "ubuntu"
            ? [
                computerTool(instance as UbuntuInstance),
                bashTool(instance as UbuntuInstance),
                editTool(instance as UbuntuInstance),
              ]
            : [computerTool(instance)];

        await client.act({
          model,
          tools,
          system:
            instanceType === "ubuntu"
              ? modelName.toLowerCase().startsWith("claude")
                ? ANTHROPIC_UBUNTU_SYSTEM_PROMPT
                : OPENAI_UBUNTU_SYSTEM_PROMPT
              : modelName.toLowerCase().startsWith("claude")
              ? ANTHROPIC_BROWSER_SYSTEM_PROMPT
              : OPENAI_BROWSER_SYSTEM_PROMPT,
          messages,
          // Send each step as a newline-delimited JSON object
          onStep: (step) => {
            controller.enqueue(`${JSON.stringify(step)}\n`);
          },
          requestOptions: {
            abortSignal: req.signal,
          },
        });
      } catch (error) {
        if (error instanceof Error) {
          controller.enqueue(`${JSON.stringify({ error: error.message })}\n`);
          console.error(error.message);
        }
        if (
          error instanceof ScrapybaraError &&
          error.message !== "The user aborted a request"
        ) {
          controller.enqueue(`${JSON.stringify({ error: error.message })}\n`);
          console.error(error.message);
        }
      } finally {
        controller.close();
      }
    },
  });

  return new Response(stream);
}
