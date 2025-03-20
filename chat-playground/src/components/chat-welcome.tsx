import { Button } from "@/components/ui/button";
import { House, Luggage, Sandwich, LucideIcon } from "lucide-react";

interface ChatWelcomeProps {
  apiKey: string;
  setInput: (input: string) => void;
}

interface PromptItem {
  title: string;
  prompt: string;
  icon: LucideIcon;
}

const prompts: PromptItem[] = [
  {
    title: "Plan Japan trip",
    prompt:
      "Plan a full travel itinerary to Japan to see cherry blossoms and capybaras. Find stays, flights, and write notes in a HTML file.",
    icon: Luggage,
  },
  {
    title: "Order chicken burger",
    prompt:
      "Order the best chicken burger on Uber Eats. Prompt me to log in if needed.",
    icon: Sandwich,
  },
  {
    title: "Rent apartment in SF",
    prompt:
      "Find studio apartments in Dogpatch, San Francisco from $2-3k. Contact the properties and ask for a tour.",
    icon: House,
  },
];

export function ChatWelcome({ apiKey, setInput }: ChatWelcomeProps) {
  return (
    <div className="flex flex-col flex-grow justify-center">
      <div className="flex flex-col gap-8 pb-16">
        <h1 className="relative text-left text-2xl font-medium w-full">
          {!apiKey
            ? "Enter your Scrapybara API key to start"
            : "How can I help?"}
        </h1>
        <div className="flex flex-col gap-1 -mx-3">
          {prompts.map((prompt, index) => (
            <div key={prompt.title}>
              <Button
                variant="ghost"
                className="flex w-full justify-start gap-2"
                onClick={() => setInput(prompt.prompt)}
                disabled={!apiKey}
              >
                <prompt.icon size={16} />
                {prompt.title}
              </Button>
              {index < prompts.length - 1 && (
                <hr className="border-border mt-1 mx-3" />
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
