import { Computer, Edit, Terminal } from "lucide-react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Scrapybara } from "scrapybara";
import { cn } from "@/lib/utils";

interface MessageProps {
  message: Scrapybara.Message;
}

export function Message({ message }: MessageProps) {
  if (
    message.role === "tool" &&
    (!message.content ||
      message.content.every(
        (part: {
          result: {
            output?: string;
            system?: string;
            error?: string;
          };
        }) => !part.result.output && !part.result.system && !part.result.error
      ))
  ) {
    return null;
  }

  return (
    <div
      className={cn(
        "flex w-max max-w-[86.9%] flex-col gap-4 py-2",
        message.role === "user" &&
          "ml-auto bg-primary text-primary-foreground px-4 rounded-lg"
      )}
    >
      {message.content && (
        <>
          {message.role === "user" && (
            <p className="whitespace-pre-wrap">
              {message.content
                .map((part) => (part.type === "text" ? part.text : ""))
                .join("")}
            </p>
          )}
          {message.role === "assistant" && (
            <>
              {message.content.map((part, i) => {
                if (part.type === "reasoning") {
                  if (!part.reasoning) return null;
                  return (
                    <div key={i} className="text-muted-foreground my-4">
                      <Markdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          ul: ({ children }) => (
                            <ul className="list-disc pl-4 py-4">{children}</ul>
                          ),
                          ol: ({ children }) => (
                            <ol className="list-decimal pl-6 py-4">
                              {children}
                            </ol>
                          ),
                        }}
                      >
                        {part.reasoning}
                      </Markdown>
                    </div>
                  );
                }
                if (part.type === "text") {
                  if (!part.text) return null;
                  return (
                    <div key={i} className="my-4">
                      <Markdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          ul: ({ children }) => (
                            <ul className="list-disc pl-4 py-4">{children}</ul>
                          ),
                          ol: ({ children }) => (
                            <ol className="list-decimal pl-6 py-4">
                              {children}
                            </ol>
                          ),
                        }}
                      >
                        {part.text}
                      </Markdown>
                    </div>
                  );
                }
                if (part.type === "tool-call") {
                  return (
                    <div
                      key={i}
                      className="flex flex-col gap-2 font-mono border border-primary rounded-lg p-2 px-4 text-sm"
                    >
                      <div className="flex items-center gap-2 font-medium text-primary">
                        {part.toolName === "computer" && (
                          <Computer size={12} strokeWidth={2.5} />
                        )}
                        {part.toolName === "str_replace_editor" && (
                          <Edit size={12} strokeWidth={2.5} />
                        )}
                        {part.toolName === "bash" && (
                          <Terminal size={12} strokeWidth={2.5} />
                        )}
                        {part.toolName}
                      </div>
                      <p className="whitespace-pre-wrap break-all">
                        {Object.entries(part.args)
                          .map(([key, value]) => `${key}: ${String(value)}`)
                          .join("\n")}
                      </p>
                    </div>
                  );
                }
                return null;
              })}
            </>
          )}
          {message.role === "tool" && (
            <>
              {message.content.map((part, i) => {
                if (!part.result || typeof part.result !== "object")
                  return null;

                const result = part.result as {
                  output?: string;
                  system?: string;
                  error?: string;
                };
                if (!result.output && !result.system && !result.error)
                  return null;

                return (
                  <div key={i}>
                    {result.output && (
                      <p className="font-mono text-sm whitespace-pre-wrap break-all">
                        {result.output}
                      </p>
                    )}
                    {result.system && (
                      <p className="font-mono text-sm whitespace-pre-wrap break-all">
                        {result.system}
                      </p>
                    )}
                    {result.error && (
                      <p className="whitespace-pre-wrap break-all text-destructive">
                        {result.error}
                      </p>
                    )}
                  </div>
                );
              })}
            </>
          )}
        </>
      )}
    </div>
  );
}
