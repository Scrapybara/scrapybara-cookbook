import { Square } from "lucide-react";
import { FaChrome, FaUbuntu } from "react-icons/fa6";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import TerminalLoader, { Loader } from "./loader";

interface InstanceFrameProps {
  instanceId: string | null;
  streamUrl: string | null;
  isStarting: boolean;
  isStopping: boolean;
  selectedInstanceType: "ubuntu" | "browser";
  handleStop: () => Promise<void>;
}

export function InstanceFrame({
  instanceId,
  streamUrl,
  isStarting,
  isStopping,
  selectedInstanceType,
  handleStop,
}: InstanceFrameProps) {
  const [elapsedTime, setElapsedTime] = useState(0);

  useEffect(() => {
    let interval: NodeJS.Timeout;

    if (instanceId && !isStarting && !isStopping) {
      // Reset timer when a new instance starts
      setElapsedTime(0);

      // Update every second
      interval = setInterval(() => {
        setElapsedTime((prev) => prev + 1);
      }, 1000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [instanceId, isStarting, isStopping]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
      .toString()
      .padStart(2, "0");
    const secs = (seconds % 60).toString().padStart(2, "0");
    return `${mins}:${secs}`;
  };

  return (
    <div className="justify-center flex flex-col w-full md:w-1/2 transition-all duration-500 ease-in-out">
      <div className="flex items-center justify-between bg-muted p-2 rounded-t-lg">
        <div className="flex items-center gap-2">
          <span className="ml-2 text-sm text-muted-foreground">
            {selectedInstanceType === "ubuntu" ? (
              <FaUbuntu className="inline mr-2" />
            ) : (
              <FaChrome className="inline mr-2" />
            )}
            {instanceId || `${selectedInstanceType} instance`}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {instanceId && !isStarting && !isStopping && (
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-primary animate-pulse flex-shrink-0"></div>
              <div className="flex items-baseline">
                <span className="text-sm tabular-nums w-10 inline-block">
                  {formatTime(elapsedTime)}
                </span>
                <span className="text-xs text-muted-foreground">/60:00</span>
              </div>
            </div>
          )}
          <Button
            variant="destructive"
            size="sm"
            onClick={handleStop}
            disabled={isStarting || isStopping || !instanceId}
          >
            {isStopping ? (
              <>Stopping</>
            ) : (
              <>
                <Square size={16} />
                Stop
              </>
            )}
          </Button>
        </div>
      </div>
      <div className={cn("w-full aspect-[4/3] rounded-b-lg overflow-hidden")}>
        {isStarting && (
          <div className="w-full h-full flex items-center justify-center bg-muted">
            <div className="flex flex-col items-center gap-4">
              <Loader />
              <p className="text-lg animate-pulse">
                Starting {selectedInstanceType} instance...
              </p>
            </div>
          </div>
        )}
        {isStopping && (
          <div className="w-full h-full flex items-center justify-center bg-muted">
            <div className="flex flex-col items-center gap-4">
              <TerminalLoader />
              <p className="text-lg animate-pulse">Stopping {instanceId}...</p>
            </div>
          </div>
        )}
        {streamUrl && !isStarting && !isStopping && (
          <iframe
            src={streamUrl}
            className="w-full h-full"
            allow="clipboard-write"
          />
        )}
      </div>
    </div>
  );
}
