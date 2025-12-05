"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  UploadCloud,
  ScanSearch,
  Settings,
  GitBranch,
  Menu,
  X
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

function SidebarNav({
  pathname,
  onNavigate
}: {
  pathname: string | null;
  onNavigate?: () => void;
}) {
  return (
    <div className="flex h-full w-full flex-col rounded-2xl border border-sky-500/30 bg-gradient-to-b from-slate-900/80 via-slate-950/80 to-slate-900/90 px-3 py-4 shadow-[0_18px_45px_rgba(15,23,42,0.85)] backdrop-blur-xl">
      <div className="mb-4 flex items-center gap-3 px-1">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-sky-500 via-cyan-400 to-blue-500 text-white shadow-lg shadow-sky-500/40 ring-1 ring-sky-500/60">
          <GitBranch className="h-5 w-5" />
        </div>
        <div className="flex flex-col">
          <span className="text-sm font-semibold tracking-tight">
            MasterGrader
          </span>
          <span className="text-[0.7rem] font-medium uppercase tracking-[0.16em] text-sky-300/80">
            C Lab Engine
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
              onClick={onNavigate}
              className={cn(
                "group relative flex items-center justify-between rounded-lg px-2 py-2 text-sm font-medium text-slate-300/90 transition-all hover:text-slate-50",
                "hover:bg-slate-800/60 hover:shadow-[0_0_0_1px_rgba(56,189,248,0.5)]",
                isActive &&
                  "bg-slate-900/80 text-sky-100 shadow-[0_0_0_1px_rgba(56,189,248,0.9)]"
              )}
            >
              <span className="flex items-center gap-2">
                <span
                  className={cn(
                    "flex h-7 w-7 items-center justify-center rounded-md border border-slate-700/60 bg-slate-900/60 text-slate-300/80 shadow-inner transition-colors group-hover:border-sky-400 group-hover:bg-slate-900 group-hover:text-sky-300",
                    isActive &&
                      "border-sky-400 bg-sky-500/20 text-sky-200"
                  )}
                >
                  <Icon className="h-[1.05rem] w-[1.05rem]" />
                </span>
                <span>{item.label}</span>
              </span>
              {item.badge ? (
                <span className="rounded-full border border-amber-500/40 bg-amber-500/15 px-2 py-[0.1rem] text-[0.65rem] font-semibold uppercase tracking-[0.16em] text-amber-300">
                  {item.badge}
                </span>
              ) : null}
            </Link>
          );
        })}
      </nav>

      <div className="mt-4 rounded-xl border border-slate-700/70 bg-slate-900/70 px-3 py-2 text-[0.7rem] text-slate-300/80 shadow-inner">
        <p className="font-medium text-slate-100/90">Session</p>
        <p>Spring 2025 • CS101 – Intro to C</p>
      </div>
    </div>
  );
}

export function Sidebar() {
  const pathname = usePathname();
  const [isMobileOpen, setIsMobileOpen] = React.useState(false);

  const closeMobile = () => setIsMobileOpen(false);

  return (
    <>
      {/* Mobile hamburger trigger */}
      <button
        type="button"
        aria-label="Open navigation"
        className="fixed left-3 top-3 z-40 inline-flex h-9 w-9 items-center justify-center rounded-full border border-sky-500/40 bg-slate-950/70 text-slate-200 shadow-lg shadow-sky-500/30 backdrop-blur md:hidden"
        onClick={() => setIsMobileOpen(true)}
      >
        <Menu className="h-4 w-4" />
      </button>

      {/* Mobile drawer / sheet */}
      <div
        className={cn(
          "fixed inset-0 z-30 transform transition-all duration-200 ease-out md:hidden",
          isMobileOpen ? "pointer-events-auto" : "pointer-events-none"
        )}
      >
        <div
          className={cn(
            "absolute inset-0 bg-slate-950/60 backdrop-blur-sm transition-opacity",
            isMobileOpen ? "opacity-100" : "opacity-0"
          )}
          onClick={closeMobile}
        />
        <div
          className={cn(
            "absolute left-0 top-0 flex h-full w-72 max-w-[80%] flex-col bg-transparent p-3 transition-transform duration-200 ease-out",
            isMobileOpen ? "translate-x-0" : "-translate-x-full"
          )}
        >
          <div className="mb-2 flex items-center justify-between px-1">
            <span className="text-xs font-semibold uppercase tracking-[0.18em] text-sky-300/80">
              Navigation
            </span>
            <button
              type="button"
              aria-label="Close navigation"
              className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-slate-700/70 bg-slate-900/80 text-slate-200 shadow"
              onClick={closeMobile}
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          <SidebarNav pathname={pathname} onNavigate={closeMobile} />
        </div>
      </div>

      {/* Desktop sidebar */}
      <aside className="app-sidebar">
        <div className="flex h-full w-full flex-col p-3">
          <SidebarNav pathname={pathname} />
        </div>
      </aside>
    </>
  );
}