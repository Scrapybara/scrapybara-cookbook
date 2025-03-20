"use client";

import { useEffect, useRef, useState } from "react";

import { ArrowUp, Github, Key, RotateCcw } from "lucide-react";
import Textarea from "react-textarea-autosize";
import type { Scrapybara } from "scrapybara";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
} from "@/components/ui/select";
import { cn, filterImages } from "@/lib/utils";
import { startInstance, stopInstance } from "@/server/actions";
import { FaChrome, FaUbuntu } from "react-icons/fa6";
import { SiAnthropic, SiOpenai } from "react-icons/si";
import { Messages } from "@/components/messages";
import { ChatWelcome } from "@/components/chat-welcome";
import { InstanceFrame } from "@/components/instance-frame";
import { Loader } from "@/components/loader";

const models = [
  {
    title: "OpenAI CUA",
    modelName: "computer-use-preview",
  },
  {
    title: "Claude 3.7 Sonnet",
    modelName: "claude-3-7-sonnet-20250219",
  },
  {
    title: "Claude 3.7 Sonnet (Thinking)",
    modelName: "claude-3-7-sonnet-20250219-thinking",
  },
  {
    title: "Claude 3.5 Sonnet",
    modelName: "claude-3-5-sonnet-20241022",
  },
];

export default function Chat() {
  const [apiKey, setApiKey] = useState("");
  const [instanceId, setInstanceId] = useState<string | null>(null);
  const [streamUrl, setStreamUrl] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState("computer-use-preview");
  const [selectedInstanceType, setSelectedInstanceType] = useState<
    "ubuntu" | "browser"
  >("ubuntu");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Scrapybara.Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [isStopping, setIsStopping] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const savedApiKey = localStorage.getItem("apiKey");
      if (savedApiKey) {
        setApiKey(savedApiKey);
      }
    }
  }, []);

  const handleApiKeySubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      const newApiKey = input.trim();
      setApiKey(newApiKey);
      // Save to localStrage
      if (typeof window !== "undefined") {
        localStorage.setItem("apiKey", newApiKey);
      }
      setInput("");
    }
  };

  const handleResetApiKey = () => {
    setApiKey("");
    if (typeof window !== "undefined") {
      localStorage.removeItem("apiKey");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!apiKey) {
      handleApiKeySubmit(e);
      return;
    }

    if (isStreaming) {
      return;
    }

    const newMessages: Scrapybara.Message[] = [
      ...messages,
      { role: "user", content: [{ type: "text", text: input }] },
    ];

    setIsStreaming(true);
    setMessages(newMessages);
    setInput("");

    abortControllerRef.current = new AbortController();

    let newInstanceId;
    if (!instanceId) {
      setIsStarting(true);
      try {
        const response = await startInstance({
          apiKey,
          instanceType: selectedInstanceType,
        });
        const parsedResponse = JSON.parse(response);

        if (parsedResponse.error) {
          throw new Error(parsedResponse.error);
        }

        const { instanceId, streamUrl } = parsedResponse as {
          instanceId: string;
          streamUrl: string;
        };
        newInstanceId = instanceId;
        setInstanceId(instanceId);
        setStreamUrl(streamUrl);
      } catch (error) {
        toast.error("Failed to start instance", {
          description: error instanceof Error && error.message,
        });
        setIsStreaming(false);
        setIsStarting(false);
        setMessages([]);
        return;
      }
      setIsStarting(false);
    }

    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        apiKey,
        instanceId: instanceId ?? newInstanceId,
        instanceType: selectedInstanceType,
        modelName: selectedModel,
        messages: newMessages,
      }),
    });

    if (!response.ok) {
      setIsStreaming(false);
      return;
    }

    const reader = response.body?.getReader();
    if (!reader) {
      setIsStreaming(false);
      return;
    }

    try {
      let buffer = "";
      while (true) {
        try {
          const { done, value } = await reader.read();
          if (done || abortControllerRef.current?.signal.aborted) break;

          // Decode and accumulate incoming chunks
          const text = new TextDecoder().decode(value);
          buffer += text;

          // Split buffer by newlines - each line is a complete JSON message
          const messages = buffer.split("\n");
          buffer = messages.pop() || ""; // Keep the incomplete chunk for next iteration

          for (const message of messages.filter(Boolean)) {
            // Skip flush pings
            if (message.startsWith(": flush")) continue;

            try {
              const data = JSON.parse(message) as Scrapybara.Message;

              if ("error" in data && typeof data.error === "string") {
                if (data.error.includes("agent credits")) {
                  toast.error("Not enough agent credits");
                } else {
                  toast.error("Server error", {
                    description: data.error,
                  });
                }
                continue;
              }

              // Handle the message based on its role
              if (data.role === "assistant") {
                setMessages((prev) => filterImages([...prev, data], 4));
              } else if (data.role === "tool") {
                setMessages((prev) => filterImages([...prev, data], 4));
              }
            } catch (e) {
              toast.error("Failed to parse message", {
                description: e instanceof Error ? e.message : "Unknown error",
              });
            }
          }
        } catch (error) {
          if (error instanceof Error) {
            toast.error("Error reading stream", {
              description: error.message,
            });
          }
          break;
        }
      }
    } finally {
      setIsStreaming(false);
      reader.releaseLock();
      abortControllerRef.current = null;
    }
  };

  const handleStop = async () => {
    if (!instanceId) return;
    setIsStopping(true);

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    try {
      const response = await stopInstance({
        apiKey,
        instanceId,
      });

      const parsedResponse = JSON.parse(response);

      if (parsedResponse.error) {
        throw new Error(parsedResponse.error);
      }

      setInstanceId(null);
      setStreamUrl(null);
      setMessages([]);
      setIsStopping(false);
      setIsStreaming(false);
    } catch (error) {
      toast.error("Failed to stop instance", {
        description: error instanceof Error && error.message,
      });
    }
  };

  return (
    <div className="w-full h-full p-4 md:p-8">
      <header className="absolute top-4 right-4 left-4 flex justify-between items-center">
        <h1 className="text-lg font-semibold">Computer Use Playground</h1>
        <div className="flex gap-2">
          {apiKey && (
            <Button
              variant="outline"
              onClick={handleResetApiKey}
              className="flex items-center gap-2"
            >
              <Key size={16} />
              <span className="hidden sm:inline">Reset API key</span>
            </Button>
          )}
          <Button variant="outline" asChild>
            <a
              href="https://github.com/scrapybara/scrapybara-cookbook/blob/main/computer-use-playground"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2"
            >
              <Github size={16} />
              <span className="hidden sm:inline">GitHub</span>
            </a>
          </Button>
        </div>
      </header>

      <div
        className={cn(
          "w-full h-full flex flex-col-reverse md:flex-row transition-all duration-500 ease-in-out md:gap-8 pt-16"
        )}
      >
        <div
          className={cn(
            "relative flex flex-col h-full transition-all duration-500 ease-in-out",
            streamUrl || isStarting ? "w-full md:w-1/2" : "w-full"
          )}
        >
          <div className="max-w-3xl w-full mx-auto flex flex-col h-full">
            {messages.length === 0 ? (
              <ChatWelcome apiKey={apiKey} setInput={setInput} />
            ) : (
              <Messages messages={messages} />
            )}

            <div className="mt-auto pt-4">
              <p className="text-center text-xs text-muted-foreground mb-2 md:block">
                Powered by{" "}
                <a
                  href="https://docs.scrapybara.com/act-sdk"
                  target="_blank"
                  className="underline"
                >
                  Scrapybara Act SDK
                </a>
              </p>
              <form
                onSubmit={handleSubmit}
                className={cn(
                  "relative flex w-full flex-col rounded-lg border transition-all duration-300 ease-in-out",
                  !apiKey && "gap-0",
                  isStreaming && "border-primary"
                )}
              >
                <Textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      if (!input.trim()) return;
                      void handleSubmit(e);
                    }
                  }}
                  placeholder={
                    !apiKey
                      ? "Enter your Scrapybara API key"
                      : `Message ${selectedModel}`
                  }
                  className={cn(
                    "flex h-14 min-h-14 w-full resize-none rounded-lg p-4 transition-colors placeholder:text-muted-foreground focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50"
                  )}
                  style={{ scrollbarWidth: "none" }}
                  minRows={1}
                  maxRows={4}
                  autoFocus
                />
                <div
                  className={cn(
                    "relative flex gap-2 transition-all duration-300 ease-in-out",
                    !apiKey || messages.length > 0
                      ? "opacity-0 h-0 p-0 m-0 overflow-hidden"
                      : "opacity-100 p-2.5"
                  )}
                >
                  <Select
                    value={selectedModel}
                    onValueChange={setSelectedModel}
                  >
                    <SelectTrigger>
                      {selectedModel === "computer-use-preview" ? (
                        <SiOpenai />
                      ) : (
                        <SiAnthropic />
                      )}
                      {models.find((m) => m.modelName === selectedModel)
                        ?.title ?? selectedModel}
                    </SelectTrigger>
                    <SelectContent>
                      {models.map((model) => (
                        <SelectItem
                          key={model.modelName}
                          value={model.modelName}
                        >
                          <div className="flex items-center gap-2">
                            {model.modelName === "computer-use-preview" ? (
                              <SiOpenai />
                            ) : (
                              <SiAnthropic />
                            )}
                            <div className="flex flex-col gap-1">
                              <span className="text-sm font-medium">
                                {model.title}
                              </span>
                              <span className="text-xs">{model.modelName}</span>
                            </div>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {!instanceId && (
                    <>
                      <Select
                        value={selectedInstanceType}
                        onValueChange={(value) =>
                          setSelectedInstanceType(value as "ubuntu" | "browser")
                        }
                      >
                        <SelectTrigger>
                          {selectedInstanceType === "ubuntu" ? (
                            <FaUbuntu />
                          ) : (
                            <FaChrome />
                          )}
                          {selectedInstanceType === "ubuntu"
                            ? "Ubuntu"
                            : "Browser"}
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="ubuntu">
                            <FaUbuntu />
                            Ubuntu
                          </SelectItem>
                          <SelectItem value="browser">
                            <FaChrome />
                            Browser
                          </SelectItem>
                        </SelectContent>
                      </Select>
                    </>
                  )}
                </div>
                <div className="flex absolute bottom-2.5 right-2.5 gap-2">
                  {messages.length > 0 && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="flex-shrink-0"
                      type="button"
                      onClick={() => {
                        setMessages([]);
                      }}
                      disabled={isStreaming || isStarting || isStopping}
                    >
                      <RotateCcw size={16} />
                    </Button>
                  )}
                  <Button
                    type="submit"
                    disabled={
                      (!input.trim() && !isStreaming) ||
                      (!apiKey && !input.trim()) ||
                      isStarting ||
                      isStopping ||
                      isStreaming
                    }
                    size="icon"
                    className="flex-shrink-0"
                  >
                    {isStreaming ? (
                      <Loader className="w-4 h-4" variant="foreground" />
                    ) : (
                      <ArrowUp size={16} />
                    )}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        </div>

        {(streamUrl || isStarting || isStopping) && (
          <InstanceFrame
            instanceId={instanceId}
            streamUrl={streamUrl}
            isStarting={isStarting}
            isStopping={isStopping}
            selectedInstanceType={selectedInstanceType}
            handleStop={handleStop}
          />
        )}
      </div>
    </div>
  );
}
