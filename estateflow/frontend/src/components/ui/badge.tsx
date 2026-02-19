import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground shadow",
        secondary: "border-transparent bg-secondary text-secondary-foreground",
        destructive: "border-transparent bg-destructive text-destructive-foreground shadow",
        outline: "text-foreground",

        // NEW VARIANTS
        success: "border-transparent bg-success text-white shadow-sm",
        warning: "border-transparent bg-warning text-foreground shadow-sm",
        info: "border-transparent bg-info text-white shadow-sm",
        accent: "border-transparent bg-accent text-accent-foreground shadow-sm",
        soft: "border-primary/20 bg-primary/10 text-primary",
        "soft-success": "border-success/20 bg-success/10 text-success",
        "soft-warning": "border-warning/20 bg-warning/10 text-warning",
        "soft-destructive": "border-destructive/20 bg-destructive/10 text-destructive",
        gradient: "border-transparent bg-gradient-to-r from-primary to-secondary text-white shadow-md",
        premium: "border-accent/30 bg-gradient-to-r from-accent/20 to-warning/20 text-foreground shadow-glow",
        muted: "border-transparent bg-muted text-muted-foreground",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
