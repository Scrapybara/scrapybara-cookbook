"use client";

import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

interface LoaderProps {
  className?: string;
  variant?: "primary" | "foreground";
}

export const Loader = ({ className, variant = "primary" }: LoaderProps) => {
  const [position, setPosition] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setPosition((prev) => (prev + 1) % 4);
    }, 300);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className={cn("relative w-6 h-6 font-mono inline-block", className)}>
      <div
        className={cn(
          "absolute inset-0 border",
          variant === "primary" ? "border-primary" : "border-foreground"
        )}
      ></div>
      <div
        className={cn(
          "absolute w-[25%] h-[25%] transition-all duration-75",
          variant === "primary" ? "bg-primary" : "bg-foreground",
          position === 0 && "top-[10%] left-[10%]",
          position === 1 && "top-[10%] right-[10%]",
          position === 2 && "bottom-[10%] right-[10%]",
          position === 3 && "bottom-[10%] left-[10%]"
        )}
      ></div>
    </div>
  );
};

export default Loader;
