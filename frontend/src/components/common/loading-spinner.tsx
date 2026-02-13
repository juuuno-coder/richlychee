import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

export function LoadingSpinner({ className }: { className?: string }) {
  return <Loader2 className={cn("h-6 w-6 animate-spin text-muted-foreground", className)} />;
}

export function PageLoading() {
  return (
    <div className="flex h-[50vh] items-center justify-center">
      <LoadingSpinner className="h-8 w-8" />
    </div>
  );
}
