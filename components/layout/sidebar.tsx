"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  UploadCloud,
  ScanSearch,
  Settings,
  GitBranch
} from "lucide-react";

import { cn } from "@/lib/utils";

type NavItem = {
  href: string;
  label: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  badge?: string;
};

const navItems: NavItem[] = [
  {
    href: "/",
    label: "Upload & Landing",
    icon: UploadCloud
  },
  {
    href: "/dashboard",
    label: "Overview",
    icon: LayoutDashboard
  },
  {
    href: "/plagiarism",
    label: "Plagiarism Engine",
    icon: ScanSearch,
    badge: "USP"
  },
  {
    href: "/settings",
    label: "Settings",
    icon: Settings
  }
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="app-sidebar">
      <div className="flex w-full flex-col border-r border-border/80 bg-card/80 px-4 py-4">
        <div className="mb-6 flex items-center gap-3 px-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-sky-500 to-blue-500 text-white shadow-soft-card">
            <GitBranch className="h-5 w-5" />
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-semibold tracking-tight">
              MasterGrader
            </span>
            <span className="text-[0.7rem] font-medium uppercase tracking-[0.16em] text-muted-foreground">
              C Programming Lab
            </span>
          </div>
        </div>

        <nav className="flex-1 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive =
              pathname === item.href ||
              (item.href !== "/" && pathname?.startsWith(item.href));

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "group flex items-center justify-between rounded-lg px-2 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted/80 hover:text-foreground",
                  isActive &&
                    "bg-muted/70 text-foreground shadow-sm ring-1 ring-sky-500/40"
                )}
              >
                <span className="flex items-center gap-2">
                  <span
                    className={cn(
                      "flex h-7 w-7 items-center justify-center rounded-md border border-transparent bg-muted/60 text-muted-foreground shadow-sm transition-colors group-hover:bg-background group-hover:text-foreground",
                      isActive &&
                        "bg-sky-500/15 text-sky-400 group-hover:bg-sky-500/20"
                    )}
                  >
                    <Icon className="h-[1.05rem] w-[1.05rem]" />
                  </span>
                  <span>{item.label}</span>
                </span>
                {item.badge ? (
                  <span className="rounded-full border border-amber-500/40 bg-amber-500/10 px-2 py-[0.1rem] text-[0.65rem] font-semibold uppercase tracking-[0.16em] text-amber-400">
                    {item.badge}
                  </span>
                ) : null}
              </Link>
            );
          })}
        </nav>

        <div className="mt-4 border-t border-border/60 pt-3 text-[0.7rem] text-muted-foreground">
          <p className="font-medium">Session:</p>
          <p>Spring 2025 • CS101 – Intro to C</p>
        </div>
      </div>
    </aside>
  );
}