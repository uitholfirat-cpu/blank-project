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
      <section className="grid gap-6 lg:grid-cols-[minmax(0,_1.6fr)_minmax(0,_1.1fr)]">
        <div className="space-y-4">
          <div className="inline-flex items-center gap-2 rounded-full border border-sky-500/40 bg-sky-500/10 px-3 py-1 text-[0.7rem] font-semibold uppercase tracking-[0.16em] text-sky-400">
            <Sparkles className="h-3.5 w-3.5" />
            <span>AI-powered C assignment analytics</span>
          </div>
          <h1 className="text-3xl font-semibold tracking-tight md:text-4xl">
            MasterGrader: automated grading and{" "}
            <span className="bg-gradient-to-r from-sky-400 to-blue-500 bg-clip-text text-transparent">
              plagiarism detection
            </span>{" "}
            for C labs.
          </h1>
          <p className="max-w-2xl text-sm text-muted-foreground">
            Drop in a full assignment export from your LMS. MasterGrader&apos;s
            Python engine will normalize C source, run plagiarism checks across
            Q1–Q6, and surface suspicious clusters in a single dashboard.
          </p>
          <div className="flex flex-wrap items-center gap-3 text-[0.75rem] text-muted-foreground">
            <div className="inline-flex items-center gap-1.5 rounded-full border border-border/80 bg-card/80 px-2.5 py-1">
              <GitBranch className="h-3 w-3 text-emerald-400" />
              <span>Token-based similarity + structural fingerprints</span>
            </div>
            <div className="inline-flex items-center gap-1.5 rounded-full border border-border/80 bg-card/80 px-2.5 py-1">
              <ShieldCheck className="h-3 w-3 text-sky-400" />
              <span>Built for C programming courses</span>
            </div>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <Card className="border-border/80 bg-card/90">
            <CardHeader>
              <CardTitle className="text-sm">Plagiarism engine</CardTitle>
              <CardDescription>Pairwise + cluster analysis</CardDescription>
            </CardHeader>
            <CardContent className="space-y-1 text-xs text-muted-foreground">
              <p>• Token-level comparison with configurable thresholds.</p>
              <p>• Ignore comments and variable names where appropriate.</p>
              <p>• Visual cheating rings with central &ldquo;source&rdquo; nodes.</p>
            </CardContent>
          </Card>
          <Card className="border-border/80 bg-card/90">
            <CardHeader>
              <CardTitle className="text-sm">Instructor-friendly</CardTitle>
              <CardDescription>
                Designed for large C programming labs
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-1 text-xs text-muted-foreground">
              <p>• Works with LMS exports and nested .zip archives.</p>
              <p>• Side‑by‑side code diff with template-aware dimming.</p>
              <p>• Dark/Light theme and responsive dashboard layout.</p>
            </CardContent>
          </Card>
        </div>
      </section>

      <UploadDropzone />
    </div>
  );
}