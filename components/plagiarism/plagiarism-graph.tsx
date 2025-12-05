"use client";

import React, { useMemo, useState } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  MarkerType,
  type Edge,
  type Node
} from "reactflow";
import "reactflow/dist/style.css";

import type { PlagiarismCase } from "@/components/report-context";
import { Slider } from "@/components/ui/slider";

type PlagiarismGraphProps = {
  cases: PlagiarismCase[];
};

const clusterColors = [
  "#38bdf8",
  "#a855f7",
  "#22c55e",
  "#eab308",
  "#f97316",
  "#f97373"
];

export function PlagiarismGraph({ cases }: PlagiarismGraphProps) {
  const [visualThreshold, setVisualThreshold] = useState<number>(90);

  const { nodes, edges } = useMemo(
    () => buildGraph(cases, visualThreshold),
    [cases, visualThreshold]
  );

  return (
    <section className="mt-6 space-y-3">
      <header className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">
            Cheating rings (graph view)
          </h2>
          <p className="text-xs text-muted-foreground">
            Nodes represent students. Edges represent highly similar submissions.
            Central nodes with many edges are likely sources.
          </p>
        </div>
        <div className="flex flex-col gap-1 text-xs sm:items-end">
          <div className="flex w-full items-center justify-between gap-3 sm:w-64">
            <span className="font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              Visual filter
            </span>
            <span className="tabular-nums text-[0.7rem] text-muted-foreground">
              ≥ {visualThreshold.toFixed(0)}%
            </span>
          </div>
          <Slider
            className="w-full sm:w-64"
            min={50}
            max={100}
            step={1}
            value={[visualThreshold]}
            onValueChange={([value]) =>
              setVisualThreshold(value ?? visualThreshold)
            }
          />
          <p className="text-[0.68rem] text-muted-foreground">
            Only render connections at or above this similarity to keep the graph
            responsive on large cohorts.
          </p>
        </div>
      </header>
      <div className="relative h-[420px] overflow-hidden rounded-xl border border-border/80 bg-card shadow-soft-card">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          fitView
          minZoom={0.4}
          maxZoom={1.8}
          panOnScroll
          zoomOnScroll
          proOptions={{ hideAttribution: true }}
        >
          <Background
            gap={22}
            color="rgba(148, 163, 184, 0.3)"
            variant="dots"
          />
          <MiniMap
            nodeStrokeColor={(n) =>
              (n.style?.borderColor as string) ?? "#38bdf8"
            }
            nodeColor={(n) =>
              (n.style?.background as string) ?? "rgba(15, 23, 42, 0.9)"
            }
            nodeBorderRadius={8}
          />
          <Controls
            position="bottom-right"
            showInteractive={false}
            className="!bg-card !border-border"
          />
        </ReactFlow>
      </div>
    </section>
  );
}

function buildGraph(
  cases: PlagiarismCase[],
  minSimilarity: number
): {
  nodes: Node[];
  edges: Edge[];
} {
  const filteredCases = cases.filter(
    (c) => c.similarity >= minSimilarity
  );

  const clusters = new Map<string, Set<string>>();

  for (const c of filteredCases) {
    if (!clusters.has(c.clusterId)) {
      clusters.set(c.clusterId, new Set());
    }
    clusters.get(c.clusterId)!.add(c.studentA);
    clusters.get(c.clusterId)!.add(c.studentB);
  }

  const nodes: Node[] = [];
  const edges: Edge[] = [];
  const studentNodeId = new Map<string, string>();

  const clusterIds = Array.from(clusters.keys());

  const clusterSpacingX = 320;
  const clusterSpacingY = 220;

  clusterIds.forEach((clusterId, clusterIndex) => {
    const students = Array.from(clusters.get(clusterId)!);
    const baseRadius = 90;
    const radius = baseRadius + students.length * 6;

    const gridX = clusterIndex % 3;
    const gridY = Math.floor(clusterIndex / 3);

    const centerX = gridX * clusterSpacingX + 160;
    const centerY = gridY * clusterSpacingY + 120;

    const color =
      clusterColors[clusterIndex % clusterColors.length] ?? "#38bdf8";

    students.forEach((student, idx) => {
      const angle = (2 * Math.PI * idx) / students.length;
      const x = centerX + radius * Math.cos(angle);
      const y = centerY + radius * Math.sin(angle);

      const id = `${clusterId}-${student}`;
      studentNodeId.set(`${clusterId}:${student}`, id);

      nodes.push({
        id,
        data: { label: student },
        position: { x, y },
        style: {
          padding: 8,
          borderRadius: 999,
          borderWidth: 1,
          borderColor: color,
          background: "rgba(15, 23, 42, 0.92)",
          color: "#e5e7eb",
          fontSize: 11,
          boxShadow:
            "0 12px 30px rgba(15, 23, 42, 0.7), 0 0 0 1px rgba(15, 23, 42, 0.9)"
        }
      });
    });
  });

  for (const c of filteredCases) {
    const sourceId = studentNodeId.get(`${c.clusterId}:${c.studentA}`);
    const targetId = studentNodeId.get(`${c.clusterId}:${c.studentB}`);
    if (!sourceId || !targetId) continue;

    const color =
      c.similarity >= 90
        ? "#f97373"
        : c.similarity >= 80
        ? "#fb923c"
        : "#eab308";

    edges.push({
      id: c.id,
      source: sourceId,
      target: targetId,
      label: `${c.questionId} • ${c.similarity.toFixed(0)}%`,
      type: "default",
      animated: c.similarity >= 90,
      style: {
        stroke: color,
        strokeWidth: 2
      },
      labelStyle: {
        fill: "#e5e7eb",
        fontSize: 10,
        fontWeight: 500
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color
      }
    });
  }

  return { nodes, edges };
}