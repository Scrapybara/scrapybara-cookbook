import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { Scrapybara } from "scrapybara";
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Filters out base64 images from messages to reduce payload size
 * Keeps only the most recent `imagesToKeep` images
 */
export function filterImages(
  messages: Scrapybara.Message[],
  imagesToKeep: number
): Scrapybara.Message[] {
  const messagesCopy = JSON.parse(
    JSON.stringify(messages)
  ) as Scrapybara.Message[];

  let imagesKept = 0;
  for (let i = messagesCopy.length - 1; i >= 0; i--) {
    const msg = messagesCopy[i];
    if (!msg) continue;
    if (msg.role === "tool" && Array.isArray(msg.content)) {
      for (let j = msg.content.length - 1; j >= 0; j--) {
        const toolResult = msg.content[j];
        if (
          toolResult?.result &&
          (toolResult.result as { base64Image?: string }).base64Image
        ) {
          if (imagesKept < imagesToKeep) {
            imagesKept++;
          } else {
            delete (toolResult.result as { base64Image?: string }).base64Image;
          }
        }
      }
    }
  }

  return messagesCopy;
}
