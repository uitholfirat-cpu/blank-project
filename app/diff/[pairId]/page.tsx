import { notFound } from "next/navigation";

import { DiffViewer } from "@/components/diff/diff-viewer";
import { plagiarismCases, professorTemplate } from "@/lib/mock-data";

export default function DiffPage({
  params
}: {
  params: { pairId: string };
}) {
  const pair = plagiarismCases.find((p) => p.id === params.pairId);

  if (!pair) {
    notFound();
  }

  return (
    <div className="space-y-6">
      <DiffViewer pair={pair} template={professorTemplate} />
    </div>
  );
}