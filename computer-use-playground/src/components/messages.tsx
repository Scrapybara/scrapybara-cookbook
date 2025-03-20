import { useEffect, useRef } from "react";
import type { Scrapybara } from "scrapybara";
import { Message } from "./message";

interface MessagesProps {
  messages: Scrapybara.Message[];
}

export function Messages({ messages }: MessagesProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  if (messages.length === 0) {
    return null;
  }

  return (
    <div
      className="flex-1 overflow-y-auto -mx-4 px-4"
      style={{
        scrollbarWidth: "thin",
        scrollbarColor: "rgba(155, 155, 155, 0.3) transparent",
        msOverflowStyle: "none",
        WebkitOverflowScrolling: "touch",
        transition: "scrollbar-color 0.3s ease",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.scrollbarColor =
          "rgba(155, 155, 155, 0.3) transparent";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.scrollbarColor =
          "rgba(155, 155, 155, 0) transparent";
      }}
    >
      <div className="flex flex-col gap-4 py-8">
        {messages.map((message, index) => (
          <Message
            key={index}
            message={message}
            isLastMessage={index === messages.length - 1}
          />
        ))}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}
