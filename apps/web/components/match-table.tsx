import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { ProbabilityStrip } from "@/components/probability-strip";
import type { PredictionRow } from "@/lib/mock-data";

const confidenceTone = {
  Low: "red",
  Medium: "amber",
  High: "green"
} as const;

export function MatchTable({ rows }: { rows: PredictionRow[] }) {
  const settledRows = rows.filter((row) => row.actualPoints !== null && row.actualPoints !== undefined);
  const totalActualPoints = settledRows.reduce((total, row) => total + (row.actualPoints ?? 0), 0);
  const averageActualPoints = settledRows.length > 0 ? totalActualPoints / settledRows.length : 0;

  return (
    <div className="border border-terminal-line">
      <div className="border-b border-terminal-line bg-terminal-panel px-3 py-2 text-xs text-terminal-muted">
        EV means expected value: the average Tipp-Spiel points this pick would score over many repeats of the
        same match distribution. A higher EV pick can differ from the single most likely scoreline.
      </div>
      <div className="grid gap-3 border-b border-terminal-line bg-terminal-bg p-3 text-sm md:grid-cols-3">
        <div>
          <div className="font-mono text-xs uppercase text-terminal-muted">Model-following points</div>
          <div className="text-xl font-semibold text-terminal-ink">{totalActualPoints}</div>
        </div>
        <div>
          <div className="font-mono text-xs uppercase text-terminal-muted">Finished tracked</div>
          <div className="text-xl font-semibold text-terminal-ink">
            {settledRows.length} / {rows.length}
          </div>
        </div>
        <div>
          <div className="font-mono text-xs uppercase text-terminal-muted">Average per finished match</div>
          <div className="text-xl font-semibold text-terminal-ink">{averageActualPoints.toFixed(2)}</div>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse text-sm">
          <thead className="bg-terminal-panel text-left font-mono text-xs uppercase text-terminal-muted">
            <tr>
              <th className="border-b border-terminal-line px-3 py-2">Date</th>
              <th className="border-b border-terminal-line px-3 py-2">Match</th>
              <th className="border-b border-terminal-line px-3 py-2">Model 1X2</th>
              <th className="border-b border-terminal-line px-3 py-2">Model Elo</th>
              <th className="border-b border-terminal-line px-3 py-2">Best Tipp EV</th>
              <th className="border-b border-terminal-line px-3 py-2">Actual</th>
              <th className="border-b border-terminal-line px-3 py-2">Most Likely</th>
              <th className="border-b border-terminal-line px-3 py-2">Confidence</th>
              <th className="border-b border-terminal-line px-3 py-2">Why</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className="bg-terminal-bg odd:bg-terminal-panel/45">
                <td className="whitespace-nowrap border-b border-terminal-line px-3 py-3 font-mono text-xs text-terminal-muted">
                  {row.date}
                </td>
                <td className="border-b border-terminal-line px-3 py-3">
                  <Link
                    href={`/matches/${row.id}`}
                    className="inline-flex items-center gap-2 font-medium text-terminal-ink hover:text-terminal-cyan"
                  >
                    {row.match}
                    <ArrowUpRight className="h-3.5 w-3.5" />
                  </Link>
                  <div className="font-mono text-xs text-terminal-muted">{row.stage}</div>
                </td>
                <td className="border-b border-terminal-line px-3 py-3">
                  <ProbabilityStrip probabilities={row.model} />
                </td>
                <td className="whitespace-nowrap border-b border-terminal-line px-3 py-3 font-mono text-xs text-terminal-muted">
                  {row.homeElo && row.awayElo ? (
                    <>
                      {row.homeElo} - {row.awayElo}
                      <div className="text-terminal-amber">
                        {row.ratingDelta && row.ratingDelta > 0 ? "+" : ""}
                        {row.ratingDelta ?? 0}
                      </div>
                      {!row.homeRatingKnown || !row.awayRatingKnown ? (
                        <div className="text-terminal-muted">neutral fallback</div>
                      ) : null}
                    </>
                  ) : (
                    "-"
                  )}
                </td>
                <td className="border-b border-terminal-line px-3 py-3 font-mono text-terminal-amber">{row.bestTip}</td>
                <td className="whitespace-nowrap border-b border-terminal-line px-3 py-3 font-mono text-xs">
                  {row.actualScore ? (
                    <div>
                      <div className="text-terminal-ink">FT {row.actualScore}</div>
                      <div className={row.actualPoints ? "text-terminal-green" : "text-terminal-muted"}>
                        {row.actualPoints ?? 0} pts
                      </div>
                    </div>
                  ) : (
                    <span className="text-terminal-muted">{row.status ?? "scheduled"}</span>
                  )}
                </td>
                <td className="border-b border-terminal-line px-3 py-3 font-mono text-terminal-muted">
                  {row.mostLikelyScore}
                </td>
                <td className="border-b border-terminal-line px-3 py-3">
                  <div className="space-y-1">
                    <Badge tone={confidenceTone[row.confidence]}>{row.confidence}</Badge>
                    {row.confidenceScore !== undefined ? (
                      <div className="font-mono text-xs text-terminal-muted">{Math.round(row.confidenceScore * 100)}%</div>
                    ) : null}
                  </div>
                </td>
                <td className="min-w-64 border-b border-terminal-line px-3 py-3 text-xs text-terminal-muted">
                  <div>{row.confidenceReason ?? "Model probability spread."}</div>
                  {row.expectedGoals ? <div className="mt-1 font-mono text-terminal-amber">xG {row.expectedGoals}</div> : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
