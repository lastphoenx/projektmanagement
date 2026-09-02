"use client";

import { useMemo, useState } from "react";
import type { PortfolioMatrixPoint } from "@/lib/portfolio-types";
import { assignPortfolioTier, tierLabel } from "@/lib/portfolio-metrics";
import { cn } from "@/lib/utils";

type BubbleMetric = "npv" | "job" | "cost";

interface PortfolioMatrixProps {
  data: PortfolioMatrixPoint[];
  bubbleMetric?: BubbleMetric;
  onSelect?: (id: string) => void;
}

const PLOT = { left: 52, top: 16, width: 320, height: 320 };

function tierFill(tier: string): string {
  switch (tier) {
    case "A":
      return "#22c55e";
    case "B":
      return "#eab308";
    case "C":
      return "#ef4444";
    default:
      return "#94a3b8";
  }
}

function bubbleRadius(point: PortfolioMatrixPoint, metric: BubbleMetric): number {
  let value = 1;
  if (metric === "npv") value = Math.max(point.size_npv ?? 0, 1);
  if (metric === "cost") value = Math.max(point.cost_total ?? 0, 1);
  if (metric === "job") value = 8;
  return Math.min(28, Math.max(10, Math.sqrt(value) / (metric === "job" ? 1 : 80)));
}

export function PortfolioMatrix({ data, bubbleMetric = "npv", onSelect }: PortfolioMatrixProps) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const points = useMemo(
    () =>
      data.map((p) => ({
        ...p,
        tier: assignPortfolioTier(p.y ?? 0, p.x ?? 0),
        cx: PLOT.left + ((p.x ?? 0) / 100) * PLOT.width,
        cy: PLOT.top + PLOT.height - ((p.y ?? 0) / 100) * PLOT.height,
        r: bubbleRadius(p, bubbleMetric),
      })),
    [data, bubbleMetric]
  );

  const hovered = points.find((p) => p.id === hoveredId);

  return (
    <div className="w-full">
      <svg viewBox="0 0 420 400" className="w-full max-w-xl mx-auto" role="img" aria-label="Portfolio-Matrix">
        <defs>
          <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">
            <path d="M 32 0 L 0 0 0 32" fill="none" stroke="#e2e8f0" strokeWidth="1" />
          </pattern>
        </defs>

        <rect
          x={PLOT.left}
          y={PLOT.top}
          width={PLOT.width}
          height={PLOT.height}
          fill="url(#grid)"
          stroke="#cbd5e1"
          rx={4}
        />

        <line
          x1={PLOT.left + PLOT.width / 2}
          y1={PLOT.top}
          x2={PLOT.left + PLOT.width / 2}
          y2={PLOT.top + PLOT.height}
          stroke="#94a3b8"
          strokeDasharray="5 5"
        />
        <line
          x1={PLOT.left}
          y1={PLOT.top + PLOT.height / 2}
          x2={PLOT.left + PLOT.width}
          y2={PLOT.top + PLOT.height / 2}
          stroke="#94a3b8"
          strokeDasharray="5 5"
        />

        <text x={PLOT.left + PLOT.width / 2} y={PLOT.top + PLOT.height + 28} textAnchor="middle" fontSize="11" fill="#64748b">
          Feasibility (Machbarkeit) →
        </text>
        <text
          x={14}
          y={PLOT.top + PLOT.height / 2}
          textAnchor="middle"
          fontSize="11"
          fill="#64748b"
          transform={`rotate(-90 14 ${PLOT.top + PLOT.height / 2})`}
        >
          Strategic Importance →
        </text>

        {points.map((p) => (
          <g
            key={p.id}
            className={cn(onSelect && "cursor-pointer")}
            onMouseEnter={() => setHoveredId(p.id)}
            onMouseLeave={() => setHoveredId(null)}
            onClick={() => onSelect?.(p.id)}
          >
            <circle
              cx={p.cx}
              cy={p.cy}
              r={p.r}
              fill={tierFill(p.tier)}
              fillOpacity={hoveredId === p.id ? 0.95 : 0.75}
              stroke={tierFill(p.tier)}
              strokeWidth={hoveredId === p.id ? 3 : 2}
            />
            <text x={p.cx} y={p.cy + 4} textAnchor="middle" fontSize="9" fill="#fff" fontWeight="600">
              {p.display_number}
            </text>
          </g>
        ))}
      </svg>

      {hovered && (
        <div className="mt-2 rounded-lg border border-border/70 bg-card px-4 py-3 text-sm shadow-card">
          <p className="font-semibold">{hovered.name}</p>
          <div className="mt-1 grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-muted-foreground">
            <span>Tier</span>
            <span className="text-foreground font-medium">{tierLabel(hovered.tier)}</span>
            <span>Feasibility</span>
            <span className="text-foreground font-medium">{(hovered.x ?? 0).toFixed(1)}%</span>
            <span>Strategic Importance</span>
            <span className="text-foreground font-medium">{(hovered.y ?? 0).toFixed(1)}%</span>
            <span>WSJF</span>
            <span className="text-foreground font-medium">{(hovered.wsjf ?? 0).toFixed(2)}</span>
          </div>
        </div>
      )}

      <div className="mt-4 grid grid-cols-2 gap-2 text-xs text-muted-foreground border-t border-border/60 pt-3">
        <div className="text-right">
          <p className="font-medium">Unten links</p>
          <p>Low Priority</p>
        </div>
        <div>
          <p className="font-medium">Unten rechts</p>
          <p>Quick &amp; Easy</p>
        </div>
        <div className="text-right">
          <p className="font-medium">Oben links</p>
          <p>Strategic Long-term</p>
        </div>
        <div>
          <p className="font-medium text-green-600">Oben rechts</p>
          <p className="text-green-600">Quick Wins (Tier A)</p>
        </div>
      </div>
    </div>
  );
}
