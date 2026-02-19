import * as React from "react";

import { cn } from "@/lib/utils";

const Input = React.forwardRef<HTMLInputElement, React.ComponentProps<"input">>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          // Base styles
          "flex h-11 w-full rounded-lg border border-input bg-background px-4 py-2 text-sm",
          // Typography
          "placeholder:text-muted-foreground",
          // Focus state with bottom border accent (Material Design style)
          "transition-all duration-200",
          "focus-visible:outline-none focus-visible:ring-0",
          "focus-visible:border-primary focus-visible:shadow-[0_2px_0_0_hsl(var(--primary))]",
          // Disabled state
          "disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-muted",
          // Hover state
          "hover:border-primary/50",
          // File input styles
          "file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground",
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";

export { Input };
