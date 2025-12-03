import { PlagiarismTable } from "@/components/plagiarism/plagiarism-table";
import { PlagiarismGraph } from "@/components/plagiarism/plagiarism-graph";
import { plagiarismCases } from "@/lib/mock-data";

export default function PlagiarismPage() {
  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-2">
        <h1 className="text-xl font-semibold tracking-tight">
          Plagiarism engine
        </h1>
        <p className="text-xs text-muted-foreground">
          Investigate suspicious pairs, then pivot into a network view of
          suspected cheating rings.
        </p>
      </header>
      <PlagiarismTable cases={plagiarismCases} />
      <PlagiarismGraph cases={plagiarismCases} />
    </div>
  );
}