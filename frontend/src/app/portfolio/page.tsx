"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { Plus } from "lucide-react";
import AppLayout from "@/components/layout/AppLayout";
import { PageContainer } from "@/components/layout/PageContainer";
import { PageHeader } from "@/components/layout/PageHeader";
import { PortfolioMatrix } from "@/components/portfolio/PortfolioMatrix";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { InlineAlert } from "@/components/ui/inline-alert";
import {
  fetchPortfolioMatrix,
  fetchPortfolioWsjf,
  type PortfolioMatrixPoint,
  type PortfolioWsjfItem,
} from "@/lib/api";
import {
  assignPortfolioTier,
  categoryIcon,
  formatChf,
  tierColorClass,
  tierLabel,
} from "@/lib/portfolio-metrics";

export default function PortfolioPage() {
  const router = useRouter();
  const [matrixData, setMatrixData] = useState<PortfolioMatrixPoint[]>([]);
  const [wsjfRanking, setWsjfRanking] = useState<PortfolioWsjfItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTier, setSelectedTier] = useState<string | null>(null);

  async function loadData() {
    try {
      setLoading(true);
      setError(null);
      const [matrix, wsjf] = await Promise.all([
        fetchPortfolioMatrix(),
        fetchPortfolioWsjf(),
      ]);
      setMatrixData(matrix);
      setWsjfRanking(wsjf);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Portfolio konnte nicht geladen werden");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const enriched = useMemo(
    () =>
      matrixData.map((p) => ({
        ...p,
        tier: assignPortfolioTier(p.y ?? 0, p.x ?? 0),
      })),
    [matrixData]
  );

  const filtered = selectedTier ? enriched.filter((p) => p.tier === selectedTier) : enriched;

  const tierStats = {
    A: enriched.filter((p) => p.tier === "A").length,
    B: enriched.filter((p) => p.tier === "B").length,
    C: enriched.filter((p) => p.tier === "C").length,
  };

  const filteredWsjf = selectedTier
    ? wsjfRanking.filter((item) => {
        const point = enriched.find((p) => p.id === item.id);
        return point?.tier === selectedTier;
      })
    : wsjfRanking;

  if (loading) {
    return (
      <AppLayout>
        <PageContainer>
          <p className="text-muted-foreground py-16 text-center">Portfolio wird geladen…</p>
        </PageContainer>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <PageContainer>
        <PageHeader
          title="Portfolio"
          description={`Strategic Matrix und WSJF-Ranking für ${enriched.length} Projekt${enriched.length === 1 ? "" : "e"}.`}
          actions={
            <Button asChild>
              <Link href="/portfolio/projects/new">
                <Plus className="w-4 h-4" />
                Neues Portfolio-Projekt
              </Link>
            </Button>
          }
        />

        {error && (
          <InlineAlert variant="error" className="mb-6">
            {error}
          </InlineAlert>
        )}

        <div className="flex flex-wrap gap-2 mb-6">
          <Button variant={selectedTier === null ? "default" : "outline"} size="sm" onClick={() => setSelectedTier(null)}>
            Alle ({enriched.length})
          </Button>
          <Button variant={selectedTier === "A" ? "default" : "outline"} size="sm" onClick={() => setSelectedTier("A")}>
            Tier A ({tierStats.A})
          </Button>
          <Button variant={selectedTier === "B" ? "default" : "outline"} size="sm" onClick={() => setSelectedTier("B")}>
            Tier B ({tierStats.B})
          </Button>
          <Button variant={selectedTier === "C" ? "default" : "outline"} size="sm" onClick={() => setSelectedTier("C")}>
            Tier C ({tierStats.C})
          </Button>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>Portfolio-Matrix</CardTitle>
                <CardDescription>Strategic Importance vs. Feasibility</CardDescription>
              </CardHeader>
              <CardContent>
                {filtered.length === 0 ? (
                  <p className="text-sm text-muted-foreground py-8 text-center">
                    Noch keine Portfolio-Einträge.{" "}
                    <Link href="/portfolio/projects/new" className="text-primary underline">
                      Erstes Projekt aufnehmen
                    </Link>
                  </p>
                ) : (
                  <PortfolioMatrix
                    data={filtered}
                    onSelect={(id) => router.push(`/portfolio/projects/${id}/edit`)}
                  />
                )}
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>WSJF-Ranking</CardTitle>
              <CardDescription>Top 10 nach WSJF</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {filteredWsjf.slice(0, 10).map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => router.push(`/portfolio/projects/${item.id}/edit`)}
                  className="w-full text-left flex items-start gap-3 p-3 rounded-lg border border-border/80 bg-muted/40 hover:bg-muted/60 transition-colors"
                >
                  <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-bold shrink-0">
                    {item.rank}
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span>{categoryIcon(item.category)}</span>
                      {item.tier && (
                        <span className={`text-xs px-2 py-0.5 rounded border ${tierColorClass(item.tier)}`}>
                          {item.tier}
                        </span>
                      )}
                    </div>
                    <p className="text-sm font-medium truncate">{item.name}</p>
                    <p className="text-xs text-muted-foreground">WSJF: {(item.wsjf ?? 0).toFixed(2)}</p>
                  </div>
                </button>
              ))}
              {filteredWsjf.length === 0 && (
                <p className="text-sm text-muted-foreground">Keine Einträge im Filter.</p>
              )}
            </CardContent>
          </Card>
        </div>

        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Alle Portfolio-Projekte</CardTitle>
          </CardHeader>
          <CardContent className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left">
                  <th className="py-3 px-4">Projekt</th>
                  <th className="py-3 px-4">Kategorie</th>
                  <th className="py-3 px-4 text-center">Tier</th>
                  <th className="py-3 px-4 text-right">WSJF</th>
                  <th className="py-3 px-4 text-right">NPV</th>
                  <th className="py-3 px-4 text-right">Kosten</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((project) => (
                  <tr
                    key={project.id}
                    className="border-b hover:bg-muted/50 cursor-pointer"
                    onClick={() => router.push(`/portfolio/projects/${project.id}/edit`)}
                  >
                    <td className="py-3 px-4 font-medium">
                      {categoryIcon(project.category)} {project.name}
                    </td>
                    <td className="py-3 px-4 text-muted-foreground">{project.category}</td>
                    <td className="py-3 px-4 text-center">
                      <span className={`text-xs px-2 py-0.5 rounded border ${tierColorClass(project.tier)}`}>
                        {tierLabel(project.tier)}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right font-semibold">{(project.wsjf ?? 0).toFixed(2)}</td>
                    <td className="py-3 px-4 text-right">{formatChf(project.size_npv ?? 0)}</td>
                    <td className="py-3 px-4 text-right">{formatChf(project.cost_total ?? 0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      </PageContainer>
    </AppLayout>
  );
}
