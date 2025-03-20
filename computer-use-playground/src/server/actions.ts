"use server";

import { BrowserInstance, ScrapybaraClient, UbuntuInstance } from "scrapybara";

export async function startInstance({
  apiKey,
  instanceType,
  authStateId,
}: {
  apiKey: string;
  instanceType: "ubuntu" | "browser";
  authStateId?: string;
}) {
  try {
    const client = new ScrapybaraClient({
      apiKey,
    });

    let instance: UbuntuInstance | BrowserInstance;

    if (instanceType === "ubuntu") {
      instance = await client.startUbuntu();
      if (authStateId) {
        await instance.browser.start();
        await instance.browser.authenticate({ authStateId });
      }
    } else {
      instance = await client.startBrowser();
      if (authStateId) {
        await instance.authenticate({ authStateId });
      }
    }

    return JSON.stringify({
      instanceId: instance.id,
      streamUrl: (await instance.getStreamUrl()).streamUrl,
    });
  } catch (error) {
    return JSON.stringify({
      error:
        error instanceof Error
          ? error.message
          : "Unknown error starting instance",
    });
  }
}

export async function stopInstance({
  apiKey,
  instanceId,
}: {
  apiKey: string;
  instanceId: string;
}) {
  try {
    const client = new ScrapybaraClient({ apiKey });

    const instance = await client.get(instanceId);

    await instance.stop();

    return JSON.stringify({ success: true });
  } catch (error) {
    return JSON.stringify({
      error:
        error instanceof Error
          ? error.message
          : "Unknown error stopping instance",
    });
  }
}

export async function getInstance({
  apiKey,
  instanceId,
}: {
  apiKey: string;
  instanceId: string;
}) {
  try {
    const client = new ScrapybaraClient({ apiKey });
    const instance = await client.get(instanceId);
    return JSON.stringify(instance);
  } catch (error) {
    return JSON.stringify({
      error:
        error instanceof Error
          ? error.message
          : "Unknown error getting instance",
    });
  }
}
