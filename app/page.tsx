import { ShieldCheck, Sparkles, GitBranch } from "lucide-react";

import { UploadDropzone } from "@/components/upload/upload-dropzone";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card";

export default function HomePage() {
  return (
    <div className="space-y-8">
      <section className="relative overflow-hidden rounded-3xl border border-sky-500/40 bg-gradient-to-br from-slate-950/95 via-slate-950/90 to-slate-900/90 p-[1px] shadow-soft-card">
        <div className="relative grid gap-8 rounded-3xl bg-slate-950/85 px-6 py-8 sm:px-8 md:grid-cols-[minmax(0,_1.6fr)_minmax(0,_1.1fr)] lg:py-10">
          {/* Glow accents for glassmorphism */}
          <div className="pointer-events-none absolute inset-0 opacity-60 [mask-image:radial-gradient(circle_at_top_left,white,transparent_60%)]">
            <div className="absolute -left-24 -top-24 h-52 w-52 rounded-full bg-sky-500/25 blur-3xl" />
            <div className="absolute -right-24 top-10 h-60 w-60 rounded-full bg-emerald-500/20 blur-3xl" />
          </div>

          <div className="relative space-y-5">
            <div className="inline-flex items-center gap-2 rounded-full border border-sky-400/40 bg-slate-900/80 px-3 py-1 text-[0.7rem] font-semibold uppercase tracking-[0.16em] text-sky-300 shadow-[0_0_0_1px_rgba(15,23,42,0.9)] backdrop-blur">
              <Sparkles className="h-3.5 w-3.5 text-sky-300" />
              <span>AI-powered C assignment analytics</span>
            </div>

            <h1 className="text-3xl font-semibold tracking-tight text-slate-50 md:text-4xl lg:text-5xl">
              Forensic-grade{" "}
              <span className="bg-gradient-to-r from-sky-400 via-cyan-400 to-blue-500 bg-clip-text text-transparent">
                plagiarism detection
              </span>{" "}
              for C programming labs.
            </h1>

            <p className="max-w-2xl text-sm leading-relaxed text-slate-300">
              Drop in a full assignment export from your LMS. MasterGrader&apos;s
              Python engine recursively unpacks archives, normalizes C source, and
              surfaces suspicious clusters in a single interactive dashboard.
            </p>

            <div className="flex flex-wrap items-center gap-3 text-[0.75rem] text-slate-300/90">
              <div className="inline-flex items-center gap-1.5 rounded-full border border-emerald-400/40 bg-emerald-500/10 px-2.5 py-1 shadow-sm shadow-emerald-500/30">
                <GitBranch className="h-3 w-3 text-emerald-300" />
                <span>Token-based similarity + structural fingerprints</span>
              </div>
              <div className="inline-flex items-center gap-1.5 rounded-full border border-sky-400/40 bg-sky-500/10 px-2.5 py-1 shadow-sm shadow-sky-500/30">
                <ShieldCheck className="h-3 w-3 text-sky-300" />
                <span>Cluster view for cheating rings</span>
              </div>
            </div>
          </div>

          <div className="relative grid gap-3 sm:grid-cols-2">
            <Card className="border border-sky-500/40 bg-slate-950/80 shadow-[0_18px_40px_rgba(15,23,42,0.85)] backdrop-blur">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">Plagiarism engine</CardTitle>
                <CardDescription className="text-[0.78rem]">
                  Strict vs. smart modes, tuned for C coursework.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-1.5 text-[0.75rem] text-slate-300/90">
                <p>• Structural tokenization that can ignore variable renames.</p>
                <p>• Comment stripping and whitespace normalization controls.</p>
                <p>• Per-question thresholds with cluster-level statistics.</p>
              </CardContent>
            </Card>

            <Card className="border border-slate-700/80 bg-slate-950/80 shadow-[0_18px_40px_rgba(15,23,42,0.85)] backdrop-blur">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">Instructor workflow</CardTitle>
                <CardDescription className="text-[0.78rem]">
                  Built to feel like a focused desktop grading console.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-1.5 text-[0.75rem] text-slate-300/90">
                <p>• Drag-and-drop LMS exports and nested .zip archives.</p>
                <p>• Side‑by‑side diff with template-aware dimming.</p>
                <p>• Dark/light theme, responsive sidebar, and keyboard-friendly UI.</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      <UploadDropzone />
    </div>
  );
}