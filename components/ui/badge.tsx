import * as React from "react";

import { cn } from "@/lib/utils";

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "outline" | "success" | "warning" | "danger";
}

const variantClasses: Record<NonNullable<BadgeProps["variant"]>, string> = {
  default:
    "border-transparent bg-accent/80 text-accent-foreground shadow-sm",
  outline:
    "border-border/60 bg-background/80 text-foreground shadow-sm",
  success:
    "border-emerald-500/40 bg-emerald-500/10 text-emerald-400",
  warning:
    "border-amber-500/40 bg-amber-500/10 text-amber-400",
  danger:
    "border-red-500/40 bg-red-500/10 text-red-400"
};

export function Badge({
  className,
  variant = "default",
  ...props
}: BadgeProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-[0.7rem] font-medium uppercase tracking-wide",
        variantClasses[variant],
        className
      )}
      {...props}
    />
  );
}