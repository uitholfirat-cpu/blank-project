"use client";

import { ModeToggle } from "@/components/theme/mode-toggle";

export function Topbar() {
  return (
    <header className="fixed top-0 left-0 right-0 z-30 border-b border-border/80 bg-gradient-to-b from-background/95 via-background/90 to-background/80 backdrop-blur md:left-64 lg:left-72">
      <div className="flex h-14 items-center justify-between px-4 md:px-6">
        <div className="flex flex-col">
          <span className="text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">
            MasterGrader • C Programming
          </span>
          <span className="text-sm text-muted-foreground">
            AI-assisted grading &amp; plagiarism detection
          </span>
        </div>
        <div className="flex items-center gap-3">
          <ModeToggle />
        </div>
      </div>
    </header>
  );
}