import { Computer, Edit, Terminal } from "lucide-react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Scrapybara } from "scrapybara";
import { cn } from "@/lib/utils";
import { motion } from "motion/react";
import Loader from "./loader";

interface MessageProps {
  message: Scrapybara.Message;
  isLastMessage?: boolean;
}

export function Message({ message, isLastMessage = false }: MessageProps) {
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
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={cn(
        "flex w-max max-w-[86.9%] flex-col gap-4 py-2.5",
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
                    <motion.div
                      key={i}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: i * 0.1, duration: 0.4 }}
                      className="text-muted-foreground my-4"
                    >
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
                    </motion.div>
                  );
                }
                if (part.type === "text") {
                  if (!part.text) return null;
                  return (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: i * 0.1, duration: 0.4 }}
                      className="my-4"
                    >
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
                    </motion.div>
                  );
                }
                if (part.type === "tool-call") {
                  return (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: i * 0.1, duration: 0.3 }}
                      className="flex flex-col gap-2 font-mono border border-primary rounded-lg py-2.5 px-4 text-sm relative"
                    >
                      {/* Show loader if this is the last message */}
                      {isLastMessage && message.role === "assistant" && (
                        <div className="absolute top-1.5 right-1.5">
                          <Loader className="w-3 h-3" />
                        </div>
                      )}
                      <div className="relative flex items-center gap-2 font-medium text-primary">
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
                    </motion.div>
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
                  <motion.div
                    key={i}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.2, duration: 0.4 }}
                  >
                    {result.output && (
                      <p className="font-mono text-sm whitespace-pre-wrap break-all border rounded-lg p-2 px-4">
                        {result.output}
                      </p>
                    )}
                    {result.system && (
                      <p className="font-mono text-sm whitespace-pre-wrap break-all border rounded-lg p-2 px-4">
                        {result.system}
                      </p>
                    )}
                    {result.error && (
                      <p className="font-mono text-sm whitespace-pre-wrap break-all text-destructive border border-destructive rounded-lg p-2 px-4">
                        {result.error}
                      </p>
                    )}
                  </motion.div>
                );
              })}
            </>
          )}
        </>
      )}
    </motion.div>
  );
}
