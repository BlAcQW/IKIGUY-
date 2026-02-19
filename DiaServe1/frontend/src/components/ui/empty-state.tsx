import { LucideIcon } from "lucide-react";
import { Button } from "@/components/ui/button";

export interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
    variant?: "default" | "gradient" | "premium" | "outline";
  };
  classNameProp?: string;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  classNameProp,
}: EmptyStateProps) {
  return (
    <div className={"flex flex-col items-center justify-center py-16 px-4 text-center " + (classNameProp || "")}>
      <div className="mb-6 rounded-full bg-gradient-to-br from-primary/10 to-secondary/10 p-6 shadow-inner-soft">
        <Icon className="h-12 w-12 text-primary" strokeWidth={1.5} />
      </div>
      <h3 className="mb-2 text-xl font-semibold text-foreground">{title}</h3>
      <p className="mb-6 max-w-sm text-sm text-muted-foreground leading-relaxed">
        {description}
      </p>
      {action && (
        <Button onClick={action.onClick} variant={action.variant || "default"} size="lg">
          {action.label}
        </Button>
      )}
    </div>
  );
}

export function PremiumEmptyState({
  icon: Icon,
  title,
  description,
  action,
  classNameProp,
}: EmptyStateProps) {
  return (
    <div className={"flex flex-col items-center justify-center py-20 px-4 text-center " + (classNameProp || "")}>
      <div className="mb-8 rounded-2xl bg-gradient-to-br from-accent/20 to-warning/20 p-8 shadow-glow animate-float">
        <Icon className="h-16 w-16 text-accent" strokeWidth={1.5} />
      </div>
      <h3 className="mb-3 text-2xl font-bold">
        <span className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
          {title}
        </span>
      </h3>
      <p className="mb-8 max-w-md text-base text-muted-foreground leading-relaxed">
        {description}
      </p>
      {action && (
        <Button onClick={action.onClick} variant={action.variant || "gradient"} size="xl">
          {action.label}
        </Button>
      )}
    </div>
  );
}
